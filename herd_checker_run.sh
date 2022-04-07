
set -e

mkdir -p ./user_tests
mkdir -p ./review_tests
mkdir -p ./assignments_archive
mkdir -p ./CompiHw1/hw1-tests/outsourced

# Read 2 parameters from command line to HW1_OUT_FILE and RESULTS_DIR
if [ $# -ne 2 ]; then
    echo "Usage: $0 HW1_OUT_FILE RESULTS_DIR"
    exit 1
fi

HW1_OUT_FILE=$1
RESULTS_DIR=$2
TESTS_DIR=CompiHw1/hw1-tests

# For each file in hw1-tests, run the test and print the result
for file in $TESTS_DIR/*.in
do
    echo "Running test $file"
    # Get only file name without dir
    baseName="$(basename "$file" .in)"
    $HW1_OUT_FILE < $file > $RESULTS_DIR/$baseName.res
    diff $TESTS_DIR/$baseName.out $RESULTS_DIR/$baseName.res
done

echo "Running outsourced tests (accuired from the group)"

for file in $TESTS_DIR/outsourced/*.in
do
    echo "Running test $file"
    # Remove extension
    baseName="$(basename "$file" .in)"
    $HW1_OUT_FILE < $file > $RESULTS_DIR/$baseName.res
    diff $TESTS_DIR/outsourced/$baseName.out $RESULTS_DIR/$baseName.res
done


echo "Running user uploaded tests (accuired from the group)"

for file in user_tests/*.in
do
    echo "Running test $file"
    # Remove extension
    baseName="$(basename "$file" .in)"
    $HW1_OUT_FILE < $file > $RESULTS_DIR/$baseName.res
    diff user_tests/$baseName.out $RESULTS_DIR/$baseName.res
done

echo "All tests done. Good job!"
