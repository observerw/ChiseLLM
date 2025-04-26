# Tutorial: Chisel Language Features for improving RTL Code Variability

## Parameterized and Configurable Modules/Bundles

Chisel `Module` or `Bundle` is just a Scala class, and you can create parameterized modules/bundles by passing any type of parameters to the constructor.

Example: Parameterized Adder

```scala
// Parameterized adder module with width parameter
class ParamAdder(n: Int) extends Module {
  // Define the IO bundle with configurable bit width
  val io = IO(new Bundle {
    val a = Input(UInt(n.W))  // Input signal with width 'n'
    val b = Input(UInt(n.W))
    val c = Output(UInt(n.W))
  })

  io.c := io.a + io.b
}

val add8 = Module(new ParamAdder(8))  // 8-bit adder
val add16 = Module(new ParamAdder(16)) // 16-bit adder
```

Or pass a case class to the module constructor as a configuration object. This is useful for encapsulating multiple parameters.

Example: Case Class for Configuration

```scala
// Define a case class to encapsulate configuration parameters
case class Config(txDepth: Int, rxDepth: Int, width: Int)

class MyModule(config: Config) extends Module {
  val io = IO(new Bundle {
    val data = Input(UInt(config.width.W))  // Input with configurable width
    val result = Output(UInt(config.width.W)) // Output with configurable width
  })

  // Use config parameters in the design
  io.result := io.data + config.txDepth.U  // Add 'txDepth' to the input data
}
```

## Lightweight Components with Functions

Functions in Chisel can be used to create lightweight hardware components, as long as the return type is a Chisel `Data` type.

Example: Adder Function

```scala
// Define a reusable adder function
def adder(x: UInt, y: UInt): UInt = { x + y }

// Use the adder function to create two adders
val sum1 = adder(a, b)  // Adder for inputs 'a' and 'b'
val sum2 = adder(c, d)  // Adder for inputs 'c' and 'd'
```

## Combinational Logic Generation

Chisel allows you to generate combinational logic dynamically using Scala constructs. This is particularly useful for creating lookup tables or ROMs.

Example: Square ROM

```scala
val table = Wire(Vec(100, UInt(8.W)))  // Create a vector of 100 elements, each 8 bits wide
for(i <- 0 until 100) {
  // Initialize the table with the square of the index
  table(i) := (((i / 10) << 4) + i % 10).U
}
io.output := table(io.address) // Output the value at the given address by simply looking up the table
```

## Type Parameters

Chisel supports type parameters, allowing you to create functions/modules that have processing logic regardless of the data type processed. This is useful for creating generic components.

Example: Multiplexer with Type Parameter

```scala
// generic multiplexer
def myMux[T <: Data](sel: Bool, tPath: T, fPath: T): T = {
  val ret = WireDefault(fPath)  // Default to 'fPath'
  when (sel) { ret := tPath }  // Select 'tPath' if 'sel' is true

  ret  // Return the selected value
}

// Use the multiplexer with UInt types
val resA = myMux(selA, 5.U, 10.U)  // Select between 5 and 10
// Use the multiplexer with Vec types
val resB = myMux(selB, VecInit(1.U, 2.U), VecInit(3.U, 4.U))  // Select between two vectors
```

## Optional Ports

Chisel allows you to conditionally generate ports based on configuration parameters.

Example: Register File with Optional Debug Port

```scala
class RegisterFile(debug: Boolean) extends Module {
  val io = IO(new Bundle {
    // ... other ports omitted
    // Optional debug port
    val dbgPort = if (debug) Some(Output(Vec(32, UInt(32.W)))) else None
  })

  // If debug is enabled, expose the entire register file
  if (debug) { io.dbgPort.get := regfile }
}
```

## Inheritance

Chisel modules are Scala classes, so you can use inheritance to factor out common behavior into a base class.

Example: Base Class for Ticker

```scala
// Define an abstract base class for a ticker
// We abstract "ticker" as a module that can output a tick signal at a certain frequency
// So all subclasses of Ticker will have common behavior but different implementations
abstract class Ticker(n: Int) extends Module {
  val io = IO(new Bundle {
    val tick = Output(Bool()))  // Output tick signal
  })
}

// Define a specific implementation of the ticker
class UpTicker(n: Int) extends Ticker(n) {
  val cntReg = RegInit(0.U(8.W))
  cntReg := cntReg + 1.U  // Increment the counter
  io.tick := cntReg === (n-1).U  // Generate a tick when the counter reaches 'n-1'
}

object Test {
  // Use type parameterization to accept any subclass of Ticker
  def testTicker[T <: Ticker](ticker: T): Unit = {
    // ...
  }
}
```

## Functional Programming

Chisel supports functional programming, allowing you to create hardware using higher-order functions like `map`, `reduce`, and `reduceTree`.

Example: Sum of Vector Using Functional Programming

```scala
val vec = VecInit(1.U, 2.U, 3.U, 4.U)
// Compute the sum of the vector using a tree of adders
val sum = vec.reduceTree(_ + _)
val min = vec.reduceTree((x, y) => Mux(x < y, x, y))
```

Example: Arbitration Tree

```scala
// Define an arbiter module with a configurable number of inputs
class Arbiter[T <: Data](n: Int, gen: T) extends Module {
  val io = IO(new Bundle {
    val in = Flipped(Vec(n, new DecoupledIO(gen)))  // Input vector of DecoupledIO
    val out = new DecoupledIO(gen)  // Single output DecoupledIO
  })

  // Use a reduction tree to arbitrate between inputs
  io.out <> io.in.reduceTree((a, b) => arbitrateSimp(a, b))
}
```
