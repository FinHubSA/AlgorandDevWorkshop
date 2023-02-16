#pragma version 8

# This smart contract creates, sells, and redeems tickets for a hypothetical event ticketing app.
# Global state schema: 2 uints, 0 bytes
# Local state schema: 1 uints, 0 bytes

const bytes TICKET_ID = "ticket_id"
const bytes TICKET_PRICE = "ticket_price"
const bytes TICKET_REDEEMED = "ticket_redeemed"

if Txn.ApplicationID == 0:
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
    exit(0)
end

block close_out:
    exit(0)
end

block update_app:
end

block delete_app:
    exit(0)
end

block main:
    switch Txn.ApplicationArgs[0]:
        "create_ticket": create_ticket
        "update_ticket_price": update_ticket_price
        "buy_ticket": buy_ticket
        "redeem_ticket": redeem_ticket
    end

    block create_ticket:
        assert(Txn.Sender == Global.CreatorAddress)
        assert(app_global_get(TICKET_ID) == 0)

        inner_txn:
            TypeEnum: Acfg
            Sender: Global.CurrentApplicationAddress
            ConfigAssetTotal: btoi(Txn.ApplicationArgs[1])
            ConfigAssetDecimals: 0
            ConfigAssetDefaultFrozen: 0
            ConfigAssetUnitName: Txn.ApplicationArgs[2]
            ConfigAssetName: Txn.ApplicationArgs[3]
            ConfigAssetManager: Global.CurrentApplicationAddress
            Fee: 0
        end

        app_global_put(TICKET_ID, Itxn.CreatedAssetID)
        app_global_put(TICKET_PRICE, btoi(Txn.ApplicationArgs[4]))
        log(itob(Itxn.CreatedAssetID))
        exit(1)
    end

    block update_ticket_price:
        assert(Txn.Sender == Global.CreatorAddress)
        app_global_put(TICKET_PRICE, Txn.ApplicationArgs[1])
        exit(1)
    end

    block buy_ticket:
        # caller must pay for the ticket
        assert(Gtxn[-1].TypeEnum == Pay)
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
        assert(Gtxn[-1].Amount == app_global_get(TICKET_PRICE))

        inner_txn:
            TypeEnum: Axfer
            Sender: Global.CurrentApplicationAddress
            XferAsset: app_global_get(TICKET_ID)
            AssetAmount: 1
            AssetReceiver: Txn.Sender
            Fee: 0
        end

        exit(1)
    end

    block redeem_ticket:
        assert(app_local_get(Txn.Sender, TICKET_REDEEMED) != 1)

        # caller must give ticket back
        assert(Gtxn[-1].TypeEnum == Axfer)
        assert(Gtxn[-1].XferAsset == app_global_get(TICKET_ID))
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].AssetReceiver == Global.CurrentApplicationAddress)
        assert(Gtxn[-1].AssetAmount == 1)

        app_local_put(Txn.Sender, TICKET_REDEEMED, 1)

        exit(1)
    end

    exit(1)
end
