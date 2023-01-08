ADMINISTRATOR_DESIGNATED_ABI = {
    "anonymous": False,
    "inputs": [
        {
            "indexed": True,
            "internalType": "address",
            "name": "adminTerminusAddress",
            "type": "address",
        },
        {
            "indexed": True,
            "internalType": "uint256",
            "name": "adminTerminusPoolId",
            "type": "uint256",
        },
    ],
    "name": "AdministratorDesignated",
    "type": "event",
}

SUBJECT_DESIGNATED_ABI = {
    "anonymous": False,
    "inputs": [
        {
            "indexed": True,
            "internalType": "address",
            "name": "subjectAddress",
            "type": "address",
        }
    ],
    "name": "SubjectDesignated",
    "type": "event",
}
