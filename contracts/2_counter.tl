#pragma version 8

# By Gary Lu - wklu99@gmail.com

# This smart contract stores and situationally increments a counter.
# Global state schema: 1 uints, 0 bytes
# Local state schema: 0 uints, 0 bytes

# Global state keys
const bytes COUNTER = "counter"

if Txn.ApplicationID == 0:
    # TODO: initialize our counter
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

    block increment_counter:
        # TODO: increment our counter in global state if its value is less than 3
        exit(1)
    end

    exit(1)
end
