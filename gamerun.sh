set -vx

for ((  i = 0 ;  i < $1;  i++  ))
do
  java -jar tools/PlayGame.jar maps/map7.txt 5000 1000 log.txt "java -jar example_bots/RandomBot.jar" "python codes/RLMABot.py $2 $3 $4" 2> "results/a${2}-${3}.out"
  NOM=`grep "Turn" results/a${2}-${3}.out | wc -l`
  WIN=`grep "Wins" results/a${2}-${3}.out`
  echo "${NOM},${WIN}">> "results/Alpha${2}Gamma${3}.txt"
  #rm -f "a${2}-${3}.out"
done

