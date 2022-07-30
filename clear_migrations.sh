set -e

wordDir=`pwd`
cd diffs/migrations
ls | grep -v __init__.py | xargs rm -rf
cd $wordDir
cd review/migrations
ls | grep -v __init__.py | xargs rm -rf
cd $wordDir