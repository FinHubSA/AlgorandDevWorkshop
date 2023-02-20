#pragma version 8

# This smart contract hosts NFT auctions for a hypothetical auction app.
# Global state schema: 2 uints, 0 bytes
# Local state schema: 3 uints, 0 bytes

struct AuctionKey:
    seller: bytes[32]
    asset_id: int
end

# Box size: 56 bytes ((int * 3) + address)
# Key size: 40 bytes (AuctionKey)
# MBR: 40900 = 2500 + 400 * (box size + key size) = 2500 + 400 * (56 + 40)
struct AuctionValue:
    end_timestamp: int
    buyout_price: int
    current_price: int
    current_bidder: bytes[32]
end

const bytes G_TOTAL_AUCTIONS = "total_auctions"
const bytes G_LIVE_AUCTIONS = "live_auctions"
const bytes L_AUCTIONS_CREATED = "auctions_created"
const bytes L_LIVE_AUCTIONS = "live_auctions"
const bytes L_AUCTIONS_WON = "auctions_won"

const bytes CREATE_AUCTION = "create_auction"
const bytes END_AUCTION = "end_auction"
const bytes PLACE_BID = "place_bid"
const bytes OPT_IN_ASSET = "opt_in_asset"

if Txn.ApplicationID == 0:
    app_global_put(G_TOTAL_AUCTIONS, 0)
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
        END_AUCTION: end_auction
        PLACE_BID: place_bid
        OPT_IN_ASSET: opt_in_asset
    end

    block create_auction:
        assert(Gtxn[-3].TypeEnum == Pay)
        assert(Gtxn[-3].Sender == Txn.Sender)
        assert(Gtxn[-3].Receiver == Global.CurrentApplicationAddress)
        # 100_000 for asset opt-in, 40900 for box MBR
        assert(Gtxn[-3].Amount == 140900)

        assert(Gtxn[-2].TypeEnum == Appl)
        assert(Gtxn[-2].Sender == Txn.Sender)
        assert(Gtxn[-2].ApplicationID == Global.CurrentApplicationID)
        assert(Gtxn[-2].OnCompletion == NoOp)
        # TODO: bug fixed, change to relative index after new pypi release is made for tealish
        assert(Gtxn[Txn.GroupIndex - 2].ApplicationArgs[0] == OPT_IN_ASSET)

        assert(Gtxn[-1].TypeEnum == Axfer)
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].AssetReceiver == Global.CurrentApplicationAddress)
        assert(Gtxn[-1].AssetAmount == 1)

        AuctionKey key = bzero(40)
        key.seller = Txn.Sender
        key.asset_id = Gtxn[-1].XferAsset

        # Implicitly asserts that the box does not already exist
        # which is important for us - we do not want a user to make
        # multiple auctions of the same asset (assumes all assets are NFTs)
        box<AuctionValue> auction = CreateBox(key)
        auction.end_timestamp = btoi(Txn.ApplicationArgs[1])
        auction.current_price = btoi(Txn.ApplicationArgs[2])
        auction.buyout_price = btoi(Txn.ApplicationArgs[3])
        # auction.current_bidder = bzero(32)

        app_global_put(G_TOTAL_AUCTIONS, (app_global_get(G_TOTAL_AUCTIONS) + 1))
        app_global_put(G_LIVE_AUCTIONS, (app_global_get(G_LIVE_AUCTIONS) + 1))
        app_local_put(Txn.Sender, L_AUCTIONS_CREATED, (app_local_get(Txn.Sender, L_AUCTIONS_CREATED) + 1))
        app_local_put(Txn.Sender, L_LIVE_AUCTIONS, (app_local_get(Txn.Sender, L_LIVE_AUCTIONS) + 1))

        exit(1)
    end

    block end_auction:
        AuctionKey key = Txn.ApplicationArgs[1]
        box<AuctionValue> auction = OpenBox(key)
        assert(auction.end_timestamp >= Global.LatestTimestamp)
        assert((Txn.Sender == key.seller) || (Txn.Sender == auction.current_bidder))

        # no one bid, close asset back to seller
        if auction.current_bidder == bzero(32):
            close_asset(key.seller, key.asset_id)
        # at least one person bid, we should settle the payment and asset transfer
        else:
            settle(key.seller, auction.current_bidder, auction.current_price, key.asset_id)
            app_local_put(auction.current_bidder, L_AUCTIONS_WON, (app_local_get(auction.current_bidder, L_AUCTIONS_WON) + 1))
        end

        decrement_auction_stats(key.seller)

        int existed = box_del(key)

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
        # We only accept the bid if it is better than the current one
        assert(Gtxn[-1].Amount > auction.current_price)

        if auction.current_bidder != bzero(32):
            # Pay back the current bidder
            inner_txn:
                TypeEnum: Pay
                Sender: Global.CurrentApplicationAddress
                Receiver: auction.current_bidder
                Amount: auction.current_price
                Fee: 0
            end
        end

        # buyout_price met, end the auction now
        if Gtxn[-1].Amount >= auction.buyout_price:
            settle(key.seller, Txn.Sender, Gtxn[-1].Amount, key.asset_id)
            decrement_auction_stats(key.seller)
            app_local_put(Txn.Sender, L_AUCTIONS_WON, (app_local_get(Txn.Sender, L_AUCTIONS_WON) + 1))
            int existed = box_del(key)
        # buyout_price not met, update the auction details
        else:
            auction.current_price = Gtxn[-1].Amount
            auction.current_bidder = Txn.Sender
        end

        exit(1)
    end

    block opt_in_asset:
        inner_txn:
            TypeEnum: Axfer
            Sender: Global.CurrentApplicationAddress
            XferAsset: Txn.Assets[btoi(Txn.ApplicationArgs[1])]
            AssetReceiver: Global.CurrentApplicationAddress
            Fee: 0
        end
        exit(1)
    end

    exit(1)
end

func settle(seller: bytes, bidder: bytes, price: int, asset_id: int):
    # Pay seller
    inner_txn:
        TypeEnum: Pay
        Sender: Global.CurrentApplicationAddress
        Receiver: seller
        Amount: price
        Fee: 0
    end

    # Close asset to bidder
    close_asset(bidder, asset_id)

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

func decrement_auction_stats(seller: bytes):
    app_global_put(G_LIVE_AUCTIONS, (app_global_get(G_LIVE_AUCTIONS) - 1))
    int auctions_created = app_local_get(seller, L_LIVE_AUCTIONS)
    if auctions_created > 0:
        app_local_put(seller, L_LIVE_AUCTIONS, (app_local_get(seller, L_LIVE_AUCTIONS) - 1))
    end

    return
end
