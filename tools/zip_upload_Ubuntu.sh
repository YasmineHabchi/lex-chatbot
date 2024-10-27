#!/bin/bash

# Variables
s3BucketName="lex-bot-template"
sourcePath="/home/yasminehabchi/Documents/GitHub/cloudformation-templates"

# Zip Python files
for file in *.py; do
    zipFileName="${file%.py}.zip"
    zipFilePath="$sourcePath/$zipFileName"
    zip -j "$zipFilePath" "$file"
done

echo "Zipping of .py files completed."

# Check if S3 bucket exists
bucketExists=$(aws s3api head-bucket --bucket "$s3BucketName" 2>&1)

# If bucket does not exist, create it
if echo "$bucketExists" | grep -q 'Not Found'; then
    aws s3 mb "s3://$s3BucketName"
    echo "Created S3 bucket: $s3BucketName"
fi

# Upload zip files to S3
for file in *.zip; do
    aws s3api put-object --bucket "$s3BucketName" --key "$file" --body "$file" --acl bucket-owner-full-control --output json
done

# Upload YAML files to S3
for file in *.yml; do
    aws s3api put-object --bucket "$s3BucketName" --key "$file" --body "$file" --acl bucket-owner-full-control --output json
done

echo "Upload of .zip and .yml files to S3 completed."

# Cleanup: Remove all .zip files from local directory
rm -f *.zip

echo "Cleanup: Removed all .zip files from local directory."

# Output URL of main.yml
outputUrl="https://$s3BucketName.s3.amazonaws.com/main.yml"
echo "$outputUrl"
