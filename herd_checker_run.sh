
set -e

# Read 3 parameters from command line to HW_OUT_FILE and RESULTS_DIR
if [ $# -ne 3 ]; then
    echo "Usage: $0 HW_OUT_FILE RESULTS_DIR HW_NUM"
    exit 1
fi

HW_NUM=$3

mkdir -p ./user_tests_hw$3
mkdir -p ./hw$3_review_tests
mkdir -p ./hw$3_archive

HW_OUT_FILE=$1
RESULTS_DIR=$2
TESTS_DIR=hw$3-tests

# For each file in hw$3-tests, run the test and print the result
for file in $TESTS_DIR/*.in
do
    echo "Running test $file"
    # Get only file name without dir
    baseName="$(basename "$file" .in)"
    $HW_OUT_FILE < $file > $RESULTS_DIR/$baseName.res 2>&1 || true
    diff $TESTS_DIR/$baseName.out $RESULTS_DIR/$baseName.res
done

echo "Running user uploaded tests (accuired from the group)"

for file in user_tests_hw$3/*.in
do
    echo "Running test $file"
    # Remove extension
    baseName="$(basename "$file" .in)"
    $HW_OUT_FILE < $file > $RESULTS_DIR/$baseName.res
    diff user_tests_hw$3/$baseName.out $RESULTS_DIR/$baseName.res
done

echo "All tests done. Good job!"
