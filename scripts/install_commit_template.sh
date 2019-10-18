#!/usr/bin/env bash
echo "Setting up commit template..."
git config --local commit.template .gitmessage
mkdir -p dumped_files # required for the app to work properly
echo "Setup Complete!!"
