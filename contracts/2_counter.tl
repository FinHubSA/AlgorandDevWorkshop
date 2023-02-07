#pragma version 8

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
        assert(Txn.Sender == Global.CreatorAddress)
        int counter_value = app_global_get(COUNTER)
        if counter_value < 3:
            app_global_put(COUNTER, counter_value + 1)
        end
        exit(1)
    end

    exit(1)
end
