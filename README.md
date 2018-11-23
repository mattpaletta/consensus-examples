# consensus-examples
Assignment for Consensus

### Vector Clocks
You can find my implementation of vector clocks in `vector_clocks.py`.  I was most interested in visually showing the 'happens before' events.  I also wanted my model to closely reflect the modelled version of a system.  I decided the closest version of this would be to model the system as follows:
```{python}
taskA = Task(name = "A")
taskB = Task(name = "B")
taskC = Task(name = "C")
```

I can represent these 'processes' sending values between each other as follows:
```{python}
taskC.send_message(taskB)
taskB.send_message(taskA)
taskB.send_message(taskC)
taskA.send_message(taskB)
taskC.send_message(taskA)
taskB.send_message(taskC)
taskC.send_message(taskA)
```

For an example of this list of messages, see: [my vector clock example](https://raw.github.com/mattpaletta/consensus-examples/master/Vector_Clocks_Example.gv.pdf)

Each task stores its own current vector clock, implemented as a dictionary in Python. Each task also stores its own name, as well as a list of previous states of its own vector clock, or counters, through time. When a task sends a message to another task, both tasks update their clocks and merge their own clocks with any information they might have received from the other one.

Finally, I have some code that collects the vector clocks at the end and plots them, drawing arrows between all the values that happened before a particular node.  After talking to some of my classmates, I realized that I should have done it differently, and iterate over the vector itself, connecting all the serial nodes in the graph, followed by matching that node with a singular (possible) event in one of the other nodes.  I ran out of time to implemement this for this assignment.

### Byzantine Generals Problem

For the byzantine generals problem, I used the opportunity that I had a sufficiently complex system to explore LLVM-JIT compilation in Python using `numba`.
The version of the algorithm I implemented is as follows:
```
- Prepare 1 commander, with the order {cmd_to_send}

- Ask the commander for consensus from the group:
- For every lieutenant (in parallel):
	- pass that message down to the lieutenant
	- that lieutenant recursively asks the other lieutenants, passing down the message it received
	- If the lieutenant is a traitor (indicated with a negative id value), it passes the alternate command, if it's at an odd index.
	- when a lieutenant receives a value, it returns the majority vote from the vote, ignoring any ties.
- The command returns the majority vote from the lieutenant
```

I know this is slightly modified the algorithm described in lamport's paper, for simplicity.

I wrap my functions in `numba.njit(nogil = True, cache = True)`. This JIT-compiles the python code into native LLVM byte-code.  The `njit` function, combined with the `nogil=True` means that LLVM doesn't use the python interpreter as part of running the code, so it's really efficient.  However, there are some restrictions.  The biggest being, you can't use any Python classes you defined, or functions outside of the standard library.  You also can't use lambda, so map and filter functions are a bit more explicit.  The 'cache=True' option is really convenient, because it automatically caches the byte-code version of your functions, so you don't pay the JIT time everytime you run your function, if you didn't change the code.  I had the option of using `jit` instead of `njit`, which still uses the python interpreter, but doesn't lock the gil when executing that code, which would allow for a broader python spec, but you loose some performance.  The other thing that numba has that I didn't explore is the option to JIT-compile a function to CUDA code or SIMD code for the CPU.

The other thing I do, just as an experiment is compute Pi to varying levels of precision, using Decimal values upto `100,000,000` digits of precision.  I was unable to get it to print more than ~200 values.
