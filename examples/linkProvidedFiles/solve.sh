#!/bin/bash
# a minimal stand-in for a solver: reads the job input and the shared mesh

inputFile=$1
shareDir=$(dirname $inputFile)

E=$(awk '$1 == "E" {print $3}' $inputFile)
Nu=$(awk '$1 == "Nu" {print $3}' $inputFile)
nNodes=$(wc -l < $shareDir/mesh/nodes.dat)
nElements=$(wc -l < $shareDir/mesh/elements.dat)

echo "E = $E, Nu = $Nu, nodes = $nNodes, elements = $nElements"

: > U.csv
: > RF.csv
for inc in $(seq 1 10); do
    u=$(awk -v inc=$inc 'BEGIN {printf "%.4f", 0.01 * inc}')
    rf=$(awk -v u=$u -v E=$E -v n=$nElements 'BEGIN {printf "%.4f", E * u * n / 1e4}')
    echo "$inc $u" >> U.csv
    echo "$inc $rf" >> RF.csv
done
