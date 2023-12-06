# Firestore Utility Tool

## Prerequisites

- Make sure python 3 is installed.
- Make sure firebase-tools are installed on your machine. If not, you will not be able to run the emulator, and receive an error.

## Setup:

In the root folder, run:

`pip3 install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org -r requirements.txt`

## fs-util Usage:

1. `--export foo,bar`

Will export "foo" and "bar" into your firestore static folder. Must be comma separated.

2. `--emulator`

Will run the firebase emulator locally, and import your firestore static folder

3. `--import`

Will import the firestore static folder to the dev project. **THIS DOES NOT DELETE.** This will only update files.

4. `--applyignore (optional)`

Adding this to the end of a usage command will apply the `.fsignore` file, and ignore the paths set there. Uses fnmatch patterns: https://docs.python.org/3/library/fnmatch.html

## .fsignore

If `*/foo` is in our ignore file, and the file directory is: `something/foo`, then the folder will be ignored. This includes exports, imports, and deletes.
If you wish to ignore only a certain file, you can do `*/foo/bar`. Notice there is no `.json` ending. This would ignore `bar.json`.

## Troubleshooting:

1. **Problem**: Export/Import hangs forever OR timeout error.

   **Solution**: Try re-authenticating yourself using `gcloud auth application-default login`

2. **Problem**: "Error: download failed, status 407"

   **Solution**: If you receive an Access denied or credentials could not be verified error on starting the emulator, try using: `firebase login`
