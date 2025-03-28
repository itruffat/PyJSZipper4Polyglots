# PYTHON EDGE CASE
# """
echo '"""'
echo 'test1"""test2'

# JS EDGE CASE
echo "*/"
echo '*/'

# LUA EDGE CASE
echo "]===]"
echo ']===]'

echo "ruby_long_string"

ruby_long_string=1
r_uby_long_stringx=2
rls=$(( ${ruby_long_string} + ${r_uby_long_stringx} ))
echo "${rls}"