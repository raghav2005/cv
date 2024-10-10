#!/bin/bash

# Define the source and target files
SOURCE=~/github_repos/cv/Resume.pdf
TARGET=~/OneDrive/Work/Resume.pdf

# Check if the target symbolic link already exists
if [ -L "$TARGET" ]; then
    # Remove the old symbolic link
    rm "$TARGET"
    echo "Old symbolic link removed."
elif [ -e "$TARGET" ]; then
    # If it's a regular file, remove it
    rm "$TARGET"
    echo "Old file removed."
fi

# Create a new symbolic link
ln -s "$SOURCE" "$TARGET"
echo "New symbolic link created: $TARGET -> $SOURCE"
