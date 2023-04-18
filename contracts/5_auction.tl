#pragma version 8

# By Gary Lu - wklu99@gmail.com

# This smart contract hosts NFT auctions for a hypothetical auction app.
# Global state schema: 2 uints, 0 bytes
# Local state schema: 3 uints, 0 bytes

# NOTE: This smart contract is relatively long and complex.
#       For workshop purposes, just go over the code

struct AuctionKey:
    seller: bytes[32]
    asset_id: int
end

# Box size: 72 bytes ((int * 5) + address)
# Key size: 40 bytes (AuctionKey)
# MBR: 47_300 = 2500 + 400 * (box size + key size) = 2500 + 400 * (72 + 40)
struct AuctionValue:
    end_timestamp: int
    buyout_price: int
    current_price: int
    current_bidder: bytes[32]
    seller_paid: int
    nft_sent: int
end

# Global state keys
const bytes G_AUCTIONS_CREATED = "auctions_created"
const bytes G_LIVE_AUCTIONS = "live_auctions"

# Local state keys
const bytes L_AUCTIONS_CREATED = "auctions_created"
const bytes L_LIVE_AUCTIONS = "live_auctions"
const bytes L_AUCTIONS_WON = "auctions_won"

# Methods
const bytes CREATE_AUCTION = "create_auction"
const bytes SETTLE = "settle"
const bytes PLACE_BID = "place_bid"

# Constants
const int MINIMUM_BID = 10000
# Box MBR + asset opt-in MBR = 47300 + 100,000
const int AUCTION_MBR_AMOUNT = 147300

if Txn.ApplicationID == 0:
    app_global_put(G_AUCTIONS_CREATED, 0)
    app_global_put(G_LIVE_AUCTIONS, 0)
    exit(1)
end

switch Txn.OnCompletion:
    NoOp: main
    OptIn: opt_in
    CloseOut: close_out
    UpdateApplication: update_app
    DeleteApplication: delete_app
end

block opt_in:
    app_local_put(Txn.Sender, L_AUCTIONS_CREATED, 0)
    app_local_put(Txn.Sender, L_LIVE_AUCTIONS, 0)
    app_local_put(Txn.Sender, L_AUCTIONS_WON, 0)
    exit(1)
end

block close_out:
    assert(app_local_get(Txn.Sender, L_LIVE_AUCTIONS) == 0)
    exit(1)
end

block update_app:
    exit(0)
end

block delete_app:
    exit(0)
end

block main:
    switch Txn.ApplicationArgs[0]:
        CREATE_AUCTION: create_auction
        SETTLE: settle
        PLACE_BID: place_bid
    end

    block create_auction:
        # Sender pays for the MBR of their box and the NFT opt-in cost the smart contract must pay
        assert(Gtxn[-1].TypeEnum == Pay)
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
        # SECURITY RISK!

        # Send NFT to contract
        assert(Gtxn[+1].TypeEnum == Axfer)
        assert(Gtxn[+1].Sender == Txn.Sender)
        assert(Gtxn[+1].AssetReceiver == Global.CurrentApplicationAddress)
        assert(Gtxn[+1].XferAsset == Txn.Assets[0])
        # SECURITY RISK!

        # Opt into the NFT being auctioned
        inner_txn:
            TypeEnum: Axfer
            Sender: Global.CurrentApplicationAddress
            XferAsset: Txn.Assets[0]
            AssetReceiver: Global.CurrentApplicationAddress
            Fee: 0
        end

        AuctionKey key = bzero(40)
        key.seller = Txn.Sender
        key.asset_id = Txn.Assets[0]

        # Implicitly asserts that the box does not already exist.
        # This is important - we do not want a user to make multiple
        # auctions of the same asset (assumes all assets are pure NFTs)
        box<AuctionValue> auction = CreateBox(key)
        auction.end_timestamp = btoi(Txn.ApplicationArgs[1])
        auction.current_price = btoi(Txn.ApplicationArgs[2])
        auction.buyout_price = btoi(Txn.ApplicationArgs[3])
        auction.seller_paid = 0
        auction.nft_sent = 0

        # The buyout price must either be greater than the base price or 0 (no buyout price)
        assert((auction.buyout_price > auction.current_price) || (auction.buyout_price == 0))

        app_global_put(G_AUCTIONS_CREATED, (app_global_get(G_AUCTIONS_CREATED) + 1))
        app_global_put(G_LIVE_AUCTIONS, (app_global_get(G_LIVE_AUCTIONS) + 1))
        app_local_put(Txn.Sender, L_AUCTIONS_CREATED, (app_local_get(Txn.Sender, L_AUCTIONS_CREATED) + 1))
        app_local_put(Txn.Sender, L_LIVE_AUCTIONS, (app_local_get(Txn.Sender, L_LIVE_AUCTIONS) + 1))

        exit(1)
    end

    block settle:
        AuctionKey key = Txn.ApplicationArgs[1]
        box<AuctionValue> auction = OpenBox(key)
        # Make sure auction isn't being ended early
        assert(Global.LatestTimestamp >= auction.end_timestamp)

        if Txn.Sender == key.seller:
            # No one bid, close asset back to seller
            if auction.current_bidder == bzero(32):
                close_asset(key.seller, key.asset_id)
                clean_up_auction(key)
            # At least one person bid, pay the seller
            else:
                # SECURITY RISK!
                pay_user(key.seller, auction.current_price)
                auction.seller_paid = 1
                if auction.nft_sent == 1:
                    clean_up_auction(key)
                end
            end
        # If the bidder ends the auction, we close the asset to them
        elif Txn.Sender == auction.current_bidder:
            # Bidder cannot be sent the NFT more than once
            assert(auction.nft_sent == 0)
            close_asset(auction.current_bidder, key.asset_id)
            app_local_put(auction.current_bidder, L_AUCTIONS_WON, (app_local_get(auction.current_bidder, L_AUCTIONS_WON) + 1))
            auction.nft_sent = 1
            if auction.seller_paid == 1:
                clean_up_auction(key)
            end
        # Sender is not the seller or the current bidder, exit
        else:
            exit(0)
        end

        exit(1)
    end

    block place_bid:
        AuctionKey key = Txn.ApplicationArgs[1]
        box<AuctionValue> auction = OpenBox(key)
        # Seller cannot bid in their own auction
        assert(Txn.Sender != key.seller)

        assert(Gtxn[-1].TypeEnum == Pay)
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
        # We only accept the bid if it is better than the current one by at least the minimum bid amount
        assert(Gtxn[-1].Amount >= (auction.current_price + MINIMUM_BID))
        # LOGICAL ERROR!

        if auction.current_bidder != bzero(32):
            # Pay back the current bidder that is being replaced
            pay_user(auction.current_bidder, auction.current_price)
        end

        # buyout_price met, end the auction now
        if (Gtxn[-1].Amount >= auction.buyout_price) && (auction.buyout_price > 0):
            pay_user(key.seller, Gtxn[-1].Amount)
            close_asset(Txn.Sender, key.asset_id)
            app_local_put(Txn.Sender, L_AUCTIONS_WON, (app_local_get(Txn.Sender, L_AUCTIONS_WON) + 1))
            clean_up_auction(key)
        # buyout_price not met, update the auction details
        else:
            auction.current_price = Gtxn[-1].Amount
            auction.current_bidder = Txn.Sender
        end

        exit(1)
    end

    exit(1)
end

func pay_user(address: bytes, amount: int):
    inner_txn:
        TypeEnum: Pay
        Sender: Global.CurrentApplicationAddress
        Receiver: address
        Amount: amount
        Fee: 0
    end

    return
end

func close_asset(address: bytes, asset_id: int):
    inner_txn:
        TypeEnum: Axfer
        Sender: Global.CurrentApplicationAddress
        XferAsset: asset_id
        AssetCloseTo: address
        Fee: 0
    end

    return
end

func clean_up_auction(key_bytes: bytes):
    AuctionKey key = key_bytes
    app_global_put(G_LIVE_AUCTIONS, (app_global_get(G_LIVE_AUCTIONS) - 1))
    int auctions_created = app_local_get(key.seller, L_LIVE_AUCTIONS)
    app_local_put(key.seller, L_LIVE_AUCTIONS, (auctions_created - 1))

    int existed = box_del(key)

    # Pay seller back the MBR increase from the auction
    inner_txn:
        TypeEnum: Pay
        Sender: Global.CurrentApplicationAddress
        Receiver: key.seller
        Amount: AUCTION_MBR_AMOUNT
        Fee: 0
    end

    return
end
