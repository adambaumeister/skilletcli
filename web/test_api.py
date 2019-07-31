from .main import GetCollections
from firestore import Firestore

def test_GetMeta():
    firestore = Firestore()
    m = firestore.get_meta()
    print(m.Get_Collections())

def test_AddCollection():
    firestore = Firestore()
    m = firestore.get_meta()
    m.Add_Collection("TestCollection")


if __name__ == "__main__":
    test_GetMeta()
    #test_AddCollection()