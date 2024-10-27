#for windows , run in powershell with command: .\zip_uplead_windows.ps1
$s3BucketName = "lex-bot-template"
$sourcePath = Get-Location


$pyFiles = Get-ChildItem -Path $sourcePath\.. -Filter *.py -Recurse
foreach ($file in $pyFiles) {
    $zipFileName = $file.BaseName + ".zip"
    $zipFilePath = Join-Path -Path $sourcePath\.. -ChildPath $zipFileName
    Compress-Archive -Path $file.FullName -DestinationPath $zipFilePath -Force
}

Write-Output "Zipping of .py files completed."

# AWS CLI command to check if bucket exists
$bucketExists = aws s3api head-bucket --bucket $s3BucketName 2>&1 | Out-String

# If bucket does not exist, create it
if ($bucketExists -match "Not Found") {
    aws s3 mb s3://$s3BucketName
    Write-Output "Created S3 bucket: $s3BucketName"
}

$zipFiles = Get-ChildItem -Path $sourcePath\.. -Filter *.zip
foreach ($file in $zipFiles) {
    aws s3api put-object --bucket $s3BucketName --key $file.Name --body $file.FullName --acl bucket-owner-full-control --output json | Out-Null
}
$ymlFiles = Get-ChildItem -Path $sourcePath\.. -Filter *.yml
foreach ($file in $ymlFiles) {
    aws s3api put-object --bucket $s3BucketName --key $file.Name --body $file.FullName --acl bucket-owner-full-control --output json | Out-Null
}

Write-Output "Upload of .zip and .yml files to S3 completed."

Remove-Item -Path "$sourcePath\..\*.zip" -Force

Write-Output "Cleanup: Removed all .zip files from local directory."

$outputUrl = "https://$s3BucketName.s3.amazonaws.com/Lex-Full-CloudformationTemplate.yml"

Write-Output $outputUrl
