import prelude.J
import prelude.A
import prelude.R


v : (i:Integer, rs:A.Array<Double>) -> i:Integer where [ i >= 0 and i <= 1 ] {
   y = A.get(rs, (2*i) + 1)   
   x = A.get(rs, 2*i)
   J.iif( ((x*x) + (y*y)) < 1, () -> 1, () -> 0)
}

main : (args:Array<String>) -> _:Void { 
   n = 1000000
   rs = R.randoms(n * 2)
   range = A.range(0,n)
   counts = A.map(range, (i:Integer) -> v(i, rs) )
   sum = A.reduce(counts, (i:Integer, j:Integer) -> i+j)
   pi = (sum * 4.0) / n
   J.out(pi)
}