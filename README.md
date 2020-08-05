# Genesis

This repository is version of Genesis modified for the experiments described in the paper, Systematically Benchmarking Example-Based ProgramTransformation Techniques on Bug-Fixing Code Changes, in which we focus on the program transformation capabilities of Genesis.

The original version of Genesis is described at https://people.csail.mit.edu/rinard/paper/fse17.genesis.pdf, can be found at http://www.cs.toronto.edu/~fanl/program_repair/genesis-rep/README.html. Genesis was developed by Long et al.

In this modified version of Genesis, we do not use test cases to guide the search for a patch. 
Instead of using defect localization, we provide the location of the defect to Genesis.
The only validation done is to check that the resulting source code of a patch compiles.

