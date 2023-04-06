#pragma version 8

# By Gary Lu - wklu99@gmail.com

# This smart contract creates and sells tickets for a hypothetical event ticketing app.
# Global state schema: 2 uints, 0 bytes
# Local state schema: 0 uints, 0 bytes

# Global state keys
const bytes TICKET_ID = "ticket_id"
const bytes TICKET_PRICE = "ticket_price"

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
    exit(0)
end

block delete_app:
    exit(0)
end

block main:
    switch Txn.ApplicationArgs[0]:
        "create_ticket": create_ticket
        "update_ticket_price": update_ticket_price
        "buy_ticket": buy_ticket
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
        app_global_put(TICKET_PRICE, btoi(Txn.ApplicationArgs[1]))
        exit(1)
    end

    block buy_ticket:
        int amount = btoi(Txn.ApplicationArgs[1])
        int price = app_global_get(TICKET_PRICE) * amount

        # Sender must pay for the ticket
        assert(Gtxn[-1].TypeEnum == Pay)
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
        assert(Gtxn[-1].Amount == price)

        inner_txn:
            TypeEnum: Axfer
            Sender: Global.CurrentApplicationAddress
            XferAsset: app_global_get(TICKET_ID)
            AssetAmount: amount
            AssetReceiver: Txn.Sender
            Fee: 0
        end

        exit(1)
    end

    exit(1)
end
