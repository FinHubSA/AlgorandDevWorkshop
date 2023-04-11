#pragma version 8

# By Gary Lu - wklu99@gmail.com

# This smart contract maintains user profiles for a hypothetical social networking app.
# Global state schema: 1 uints, 0 bytes
# Local state schema: 0 uints, 1 bytes

# Box size: 38 bytes = 10 + 20 + 8 (int is 64 bits = 8 bytes)
# Key size: 32 bytes (always an address)
# MBR: 30500 = 2500 + 400 * (box size + key size) = 2500 + 400 * (38 + 32)
# birthday field intended format is dd/mm/yyyy
struct UserInfo:
    birthday: bytes[10]
    favourite_colour: bytes[20]
    number_of_pets: int
end

# Global state keys
const bytes USERS = "users"
# Local state keys
const bytes STATUS = "status"

if Txn.ApplicationID == 0:
    # TODO: initialize our number of users
    app_global_put(USERS, 0)
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
    # TODO: expect a payment txn to cover the MBR of the box we will create
    assert(Gtxn[-1].TypeEnum == Pay)
    assert(Gtxn[-1].Sender == Txn.Sender)
    assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
    assert(Gtxn[-1].Amount == 30500)

    # TODO: create the box to store user info
    bytes birthday = Txn.ApplicationArgs[0]
    bytes favourite_colour = Txn.ApplicationArgs[1]
    int number_of_pets = btoi(Txn.ApplicationArgs[2])

    box<UserInfo> info_box = CreateBox(Txn.Sender)
    info_box.birthday = birthday
    info_box.favourite_colour = favourite_colour
    info_box.number_of_pets = number_of_pets

    # TODO: initialize user status
    app_local_put(Txn.Sender, STATUS, "")

    # TODO: increment users
    app_global_put(USERS, app_global_get(USERS) + 1)
    exit(1)
end

block close_out:
    # TODO: decrement users
    app_global_put(USERS, app_global_get(USERS) - 1)
    exit(1)
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
        "update_user_info": update_user_info
        "set_status": set_status
    end

    block update_user_info:
        # TODO: update user's box
        bytes birthday = Txn.ApplicationArgs[1]
        bytes favourite_colour = Txn.ApplicationArgs[2]
        int number_of_pets = btoi(Txn.ApplicationArgs[3])

        box<UserInfo> info_box = OpenBox(Txn.Sender)
        info_box.birthday = birthday
        info_box.favourite_colour = favourite_colour
        info_box.number_of_pets = number_of_pets
        exit(1)
    end

    block set_status:
        # TODO: set user status in local state
        app_local_put(Txn.Sender, STATUS, Txn.ApplicationArgs[1])
        exit(1)
    end

    exit(1)
end
