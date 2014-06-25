import logging
import zeroflo as flo


"""
Fibonacci Flow
--------------

it consists of two simple units:
- Add unit adds values from two diffrent inports
- Lag unit delays the output

A simple printer is used to show the results


Here's the flow diagram showing the wireing:
```
  ~ space {add} ~     | ~ space {print,lag} ~
                      |
                      |
   .---------------.  |
  :               _.` |
  `-> a][add][out ----|--> ins][print]
  .-> b]          `.  |    
  :                 `-|--> ins][delay][out -.
  `-------------------|---------------------`
                      |
```
The distribute into different process spaces is arbitrary,
but shows how easy it es to setup distributed flows.
"""

class Lag(flo.Unit):
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.setup = False

    @flo.outport
    def out(i, tag): pass

    @flo.inport
    def ins(self, i, tag):
        if self.setup:
            yield from self.last >> tag >> self.out
        else:
            self.setup = True

        self.last = i


class Add(flo.Unit):
    @flo.outport
    def out(i, tag): pass

    @flo.combine
    def add(self, a, b, tag):
        yield from a + b >> tag >> self.out

    @flo.async
    @flo.inport
    def a(self, a, tag):
        yield from self.add(a=a, tag=tag)

    @flo.async
    @flo.inport
    def b(self, b, tag):
        yield from self.add(b=b, tag=tag)


class Print(flo.Unit):
    @flo.inport
    def ins(self, o, tag):
        print('>>', o)
        if o > 1e18:
            raise ValueError("raising to show how to debug")

def setup_logging():
    logging.basicConfig(format='[%(process)d] %(levelname)5s %(message)s')
    logging.getLogger('zeroflo').setLevel("INFO")
    #logging.getLogger('zeroflo.tools').setLevel("DEBUG")
    #logging.getLogger('zeroflo.core.flow').setLevel("DEBUG")


if __name__ == "__main__":
    from examples.fib import *

    with flo.context('fib', setup=setup_logging) as ctx:
        # create flow units
        add = Add()
        lag = Lag()
        prt = Print()

        # connect flow units
        add.out >> add.a
        add.out >> lag.ins
        lag.out >> add.b

        add.out >> prt.ins

        # specifiy distribution
        add | lag & prt

    # simple call to trigger flow
    add.out(0)
    print('--')
    add.b(1)