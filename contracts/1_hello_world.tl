#pragma version 8

# A simple smart contract that logs "Hello, world!".
# Global state schema: 0 uints, 0 bytes
# Local state schema: 0 uints, 0 bytes

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
        "greeting": greeting
    end

    block greeting:
        log("Hello, world!")
        exit(1)
    end

    exit(1)
end
