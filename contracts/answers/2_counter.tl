#pragma version 8

# By Gary Lu - wklu99@gmail.com

# This smart contract stores and increments a counter if its value is less than 3.
# Global state schema: 1 uints, 0 bytes
# Local state schema: 0 uints, 0 bytes

# Global state keys
const bytes COUNTER = "counter"

if Txn.ApplicationID == 0:
    app_global_put(COUNTER, 0)
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
        "increment_counter": increment_counter
    end

    block increment_counter:
        int counter_value = app_global_get(COUNTER)
        if counter_value < 3:
            app_global_put(COUNTER, counter_value + 1)
        end
        exit(1)
    end

    exit(1)
end
