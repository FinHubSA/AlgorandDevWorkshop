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
    # TODO: route to the correct block of code based on the first argument
    switch Txn.ApplicationArgs[0]:
    end

    block create_ticket:
        # TODO: assertions

        # TODO: create ticket ASA

        # TODO: update global state
        exit(1)
    end

    block update_ticket_price
        # TODO: update ticket_price
        exit(1)
    end

    block buy_ticket:
        # TODO: get ticket amount and calculate price

        # TODO: check for payment txn

        # TODO: send ticket(s)
        exit(1)
    end

    exit(1)
end
