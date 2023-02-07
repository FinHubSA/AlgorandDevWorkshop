#pragma version 8

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
        assert(app_global_get(TICKET_ID) == 0)

        inner_txn:
            TypeEnum: Acfg
            Sender: Global.CurrentApplicationAddress
            AssetTotal: btoi(Txn.ApplicationArgs[1])
            AssetDecimals: 0
            AssetDefaultFrozen: 0
            AssetUnitName: Txn.ApplicationArgs[2]
            AssetName: Txn.ApplicationArgs[3]
            AssetManager: Global.CurrentApplicationAddress
        end

        app_global_put(TICKET_ID, Itxn.CreatedAssetID)
        app_global_put(TICKET_PRICE, Txn.ApplicationArgs[4])
        exit(1)
    end

    block update_ticket_price:
        assert(app_global_get(TICKET_ID) != 0)
        app_global_put(TICKET_PRICE, Txn.ApplicationArgs[1])
        exit(1)
    end

    block buy_ticket:
        int id = app_global_get(TICKET_ID)
        assert(id != 0)
        # caller must pay for the ticket
        assert(Gtxn[-1].TypeEnum == Pay)
        assert(Gtxn[-1].Sender == Txn.Sender)
        assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
        assert(Gtxn[-1].Amount == app_global_get(TICKET_PRICE))

        inner_txn:
            TypeEnum: Axfer
            Sender: Global.CurrentApplicationAddress
            XferAsset: id
            AssetAmount: 1
            AssetReceiver: Txn.Sender
        end

        exit(1)
    end

    exit(1)
end
