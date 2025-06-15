#!/bin/bash

echo "🔍 S3 Bucket Debug Script"
echo "========================="

# Load environment
source .env 2>/dev/null || echo "Warning: .env not found"

BUCKET="dbm-security-rag-documents"
echo "🪣 Bucket: $BUCKET"
echo "🌍 Region: ${AWS_REGION:-us-east-1}"
echo ""

echo "1️⃣ Listing bucket contents (all methods):"
echo "----------------------------------------"

echo "📋 Method 1: aws s3 ls (recursive)"
aws s3 ls s3://$BUCKET --recursive || echo "❌ Failed"

echo ""
echo "📋 Method 2: aws s3 ls (non-recursive)"
aws s3 ls s3://$BUCKET/ || echo "❌ Failed"

echo ""
echo "📋 Method 3: aws s3api list-objects-v2"
aws s3api list-objects-v2 --bucket $BUCKET --query 'Contents[].{Key:Key,Size:Size,LastModified:LastModified}' --output table 2>/dev/null || echo "❌ No objects or failed"

echo ""
echo "📋 Method 4: Check documents/ folder specifically"
aws s3 ls s3://$BUCKET/documents/ || echo "❌ No documents folder or failed"

echo ""
echo "2️⃣ Bucket information:"
echo "----------------------"

echo "📍 Bucket location:"
aws s3api get-bucket-location --bucket $BUCKET || echo "❌ Failed to get location"

echo ""
echo "🔐 Bucket policy (if any):"
aws s3api get-bucket-policy --bucket $BUCKET --query Policy --output text 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "ℹ️ No bucket policy or access denied"

echo ""
echo "📊 Bucket versioning:"
aws s3api get-bucket-versioning --bucket $BUCKET || echo "❌ Failed to get versioning info"

echo ""
echo "3️⃣ Testing upload right now:"
echo "-----------------------------"

TEST_FILE="debug-test-$(date +%s).txt"
echo "This is a debug test file created at $(date)" > $TEST_FILE

echo "📤 Uploading test file: $TEST_FILE"
if aws s3 cp $TEST_FILE s3://$BUCKET/documents/$TEST_FILE; then
    echo "✅ Upload successful"
    
    echo "📥 Checking if file appears immediately:"
    aws s3 ls s3://$BUCKET/documents/$TEST_FILE || echo "❌ File not found immediately"
    
    echo "⏳ Waiting 5 seconds and checking again:"
    sleep 5
    aws s3 ls s3://$BUCKET/documents/$TEST_FILE || echo "❌ File still not found"
    
    echo "🗑️ Cleaning up test file:"
    aws s3 rm s3://$BUCKET/documents/$TEST_FILE || echo "❌ Failed to delete"
else
    echo "❌ Upload failed"
fi

rm -f $TEST_FILE

echo ""
echo "4️⃣ User identity and permissions:"
echo "---------------------------------"
echo "👤 Current AWS identity:"
aws sts get-caller-identity || echo "❌ Failed to get identity"

echo ""
echo "🔍 Summary:"
echo "----------"
echo "If you see files above but not in AWS Console, possible causes:"
echo "1. Console showing wrong region"
echo "2. Console user different from CLI user"
echo "3. Console permissions issue"
echo "4. Browser cache issue"
echo "5. Console filtering/search issue"
echo ""
echo "Try these in AWS Console:"
echo "• Check region selector (top-right)"
echo "• Clear browser cache/refresh"
echo "• Check if you're logged in as same user"
echo "• Try different browser/incognito mode"
