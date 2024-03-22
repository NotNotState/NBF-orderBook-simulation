import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

def DateTimeFromUTC(epoch: int) -> str:
    ns = "."+str(epoch)[-9:]
    convert = datetime.utcfromtimestamp(epoch // 1000000000).strftime("%Y-%m-%d %H:%M:%S")
    convert += ns
    #return convert
    return convert[11:]

#Primary Functions
def read_transactions(file: str):
    with open(file, "r") as read_file:
        return json.load(read_file)