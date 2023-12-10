#!/usr/bin/env python3

import urllib.request
import os, sys, json, fnmatch, subprocess
from pathlib import Path
from time import sleep
import firebase_admin
from firebase_admin import firestore

ROOT_FOLDER = "firestore_static"
PROJECT = "wiiq-proj"
LOCAL_ENDPOINT = "localhost:8080"


class Firebase:
    def __init__(self):
        self.ignorePatterns = []
        if sys.argv[len(sys.argv) - 1] == "--applyignore":
            with open(".fsignore") as file:
                self.ignorePatterns = [line.rstrip() for line in file]
        firebase_admin.initialize_app()
        self.db = firestore.Client(project=PROJECT)

    def ignorePath(self, path):
        for pattern in self.ignorePatterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def imports(self):
        sys.stdout.write("Importing: ")
        # Walks through our local folder, and writes all the files to firestore
        for root, _, files in os.walk(ROOT_FOLDER, topdown=False):
            if self.ignorePath(root) or root == ROOT_FOLDER:
                continue
            for file in files:
                with open(root + "/" + file) as f:
                    data = json.load(f)
                    name = os.path.splitext(file)[0]
                    self.db.collection(root.removeprefix(ROOT_FOLDER + "/")).document(
                        name
                    ).set(data)
                sys.stdout.write(".")
        print("Import completed")

    def exports(self, collections):
        # Export all data from our selected collections
        for collection in collections:
            sys.stdout.write(f"Exporting: [{collection}]")
            self.executeOnRemoteCollections(collection, "export")
            print("Done")
        print("Export completed")

    def deletes(self):
        sys.stdout.write("Deleting: ")
        # Delete all documents not in our local static folder
        for delete in [item for item in os.listdir(ROOT_FOLDER)]:
            self.executeOnRemoteCollections(delete, "delete")
        print("Delete completed")

    def executeOnRemoteCollections(self, item, mode):
        # This functions loops through all the files/subcollections in a collection
        # It then will preform an action on those items (export/delete)
        path = ROOT_FOLDER + "/" + item
        if self.ignorePath(path):
            return
        root_ref = self.db.collection(item)
        docs = root_ref.stream()
        # Loop through all the documents in this collection
        for doc in docs:
            data = doc.to_dict()
            doc_id = doc.id
            path_with_doc_id = path + "/" + doc_id
            if self.ignorePath(path_with_doc_id):
                continue
            match mode:
                case "delete":
                    # delete files not in our static folder
                    if not os.path.isfile(
                        path_with_doc_id + ".json"
                    ) and not os.path.isdir(path_with_doc_id):
                        root_ref.document(doc_id).delete()
                        sys.stdout.write(".")
                case "export":
                    # export files
                    try:
                        os.makedirs(path)
                    except OSError as _:
                        pass
                    Path(path_with_doc_id + ".json").write_text(
                        json.dumps(data, indent=2, default=str)
                    )
                    sys.stdout.write(".")
                case _:
                    pass
            # Continue down subcollections in collection
            for collection_ref in doc.reference.collections():
                self.executeOnRemoteCollections(
                    collection_ref.parent.path + "/" + collection_ref.id, mode
                )


#########################


def main():
    match sys.argv[1]:
        case "--export":
            collections = []
            if len(sys.argv) >= 3:
                collections = sys.argv[2].split(",")
            Firebase().exports(collections)
        case "--emulator":
            emulate()
        case "--import":
            f = Firebase()
            if len(sys.argv) >= 3 and sys.argv[2] == "--delete":
                f.deletes()  # Delete remote files first
            f.imports()  # import our new ones
        case _:
            print("Invalid command.")


def emulate():
    os.environ["FIRESTORE_EMULATOR_HOST"] = LOCAL_ENDPOINT
    pro = subprocess.Popen(
        [
            "firebase",
            "emulators:start",
            "--only",
            "firestore",
            "--project",
            PROJECT,
        ],
        shell=True # Windows compatibility
    )

    def waitForEmu():
        print(f"{bcolors.BLUE}---- Waiting for emulator ----{bcolors.ENDC}")
        for _ in range(24):
            try:
                print(urllib.request.urlopen("http://" + LOCAL_ENDPOINT).read())
                return
            except:
                if pro.poll() is not None:
                    break
                sleep(5)
        raise Exception("Could not load emulator")

    def importLocalCollections():
        print(f"{bcolors.YELLOW}---- Emulator found, writing data ----{bcolors.ENDC}")
        Firebase().imports()  # import local data to emulator

    def letEmuRun():
        print(f"{bcolors.GREEN}---- Emulator is up. Go code! ----{bcolors.ENDC}")
        try:
            pro.wait()
        except:
            pass

    try:
        waitForEmu()
        importLocalCollections()
        letEmuRun()
    except Exception as e:
        print(f"{bcolors.RED}Error: {str(e)}\n---- Shutting down ----{bcolors.ENDC}")
        pro.terminate()  # Send the signal to the process
    sleep(1)


#########################


class bcolors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
