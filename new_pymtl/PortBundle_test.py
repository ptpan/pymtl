#=========================================================================
# PortBundle Test Suite
#=========================================================================

from Model          import *
from SimulationTool import *

from PortBundle     import PortBundle, create_PortBundles

import new_pmlib

#-------------------------------------------------------------------------
# Example PortBundle
#-------------------------------------------------------------------------

class ValRdyBundle( PortBundle ):
  def __init__( s, nbits ):
    s.msg = InPort  ( nbits )
    s.val = InPort  ( 1 )
    s.rdy = OutPort ( 1 )

InValRdyBundle, OutValRdyBundle = create_PortBundles( ValRdyBundle )

#-------------------------------------------------------------------------
# Example Module using PortBundle
#-------------------------------------------------------------------------

class PortBundleQueue( Model ):

  def __init__( s, nbits ):

    s.enq   = InValRdyBundle( nbits )
    s.deq   = OutValRdyBundle( nbits )

    s.full  = Wire( 1 )
    s.wen   = Wire( 1 )

  def elaborate_logic( s ):

    s.full  = Wire( 1 )
    s.wen   = Wire( 1 )

    @s.combinational
    def comb():

      s.wen.v       = ~s.full.v & s.enq.val.v
      s.enq.rdy.v   = ~s.full.v
      s.deq.val.v   = s.full.v

    @s.posedge_clk
    def seq():

      # Data Register
      if s.wen.v:
        s.deq.msg.next = s.enq.msg.v

      # Full Bit
      if s.reset.v:
        s.full.next = 0
      elif   s.deq.rdy.v and s.deq.val.v:
        s.full.next = 0
      elif s.enq.rdy.v and s.enq.val.v:
        s.full.next = 1
      else:
        s.full.next = s.full.v


  def line_trace( s ):

    return "{} {} {} () {} {} {}"\
      .format( s.enq.msg, s.enq.val, s.enq.rdy,
               s.deq.msg, s.deq.val, s.deq.rdy )

#-------------------------------------------------------------------------
# Test Elaboration
#-------------------------------------------------------------------------

from Model_test import verify_signals, verify_submodules, verify_edges

def test_elaboration():

  m = PortBundleQueue( 8 )
  m.elaborate()

  verify_signals( m.enq.get_ports(),[('enq.msg', 8), ('enq.val', 1), ('enq.rdy', 1),] )
  verify_signals( m.deq.get_ports(),[('deq.msg', 8), ('deq.val', 1), ('deq.rdy', 1),] )

  verify_signals( m.get_inports(),  [('enq.msg', 8), ('enq.val', 1), ('deq.rdy', 1),
                                     ('clk', 1), ('reset', 1)] )
  verify_signals( m.get_outports(), [('deq.msg', 8), ('deq.val', 1), ('enq.rdy', 1)] )
  verify_signals( m.get_wires(),    [('full', 1), ('wen', 1 )] )
  verify_submodules( m.get_submodules() , [] )
  verify_edges( m.get_connections(), [] )

#-------------------------------------------------------------------------
# Example Module Connecting PortBundles
#-------------------------------------------------------------------------

class TwoQueues( Model ):

  def __init__( s, nbits ):

    s.nbits = nbits

    s.in_ = InValRdyBundle ( nbits )
    s.out = OutValRdyBundle( nbits )

  def elaborate_logic( s ):

    s.q1 = PortBundleQueue( s.nbits )
    s.q2 = PortBundleQueue( s.nbits )

    s.connect( s.in_,    s.q1.enq )
    s.connect( s.q1.deq, s.q2.enq )
    s.connect( s.q2.deq, s.out    )

#-------------------------------------------------------------------------
# Test Elaboration
#-------------------------------------------------------------------------

def test_connect():

  m = TwoQueues( 8 )
  m.elaborate()
  verify_signals( m.get_inports(),  [('in_.msg', 8), ('in_.val', 1), ('out.rdy', 1),
                                     ('clk', 1), ('reset', 1)] )
  verify_signals( m.get_outports(), [('out.msg', 8), ('out.val', 1), ('in_.rdy', 1)] )
  verify_signals( m.get_wires(),    [] )
  verify_submodules( m.get_submodules() , [m.q1, m.q2] )
  verify_edges( m.get_connections(), [ ConnectionEdge( m.clk,        m.q1.clk     ),
                                       ConnectionEdge( m.reset,      m.q1.reset   ),
                                       ConnectionEdge( m.clk,        m.q2.clk     ),
                                       ConnectionEdge( m.reset,      m.q2.reset   ),

                                       ConnectionEdge( m.in_.msg,    m.q1.enq.msg ),
                                       ConnectionEdge( m.in_.val,    m.q1.enq.val ),
                                       ConnectionEdge( m.q1.enq.rdy, m.in_.rdy    ),

                                       ConnectionEdge( m.q1.deq.msg, m.q2.enq.msg ),
                                       ConnectionEdge( m.q1.deq.val, m.q2.enq.val ),
                                       ConnectionEdge( m.q2.enq.rdy, m.q1.deq.rdy ),

                                       ConnectionEdge( m.q2.deq.msg, m.out.msg    ),
                                       ConnectionEdge( m.q2.deq.val, m.out.val    ),
                                       ConnectionEdge( m.out.rdy,    m.q2.deq.rdy ),
                                     ] )

#-------------------------------------------------------------------------
# Test Sim
#-------------------------------------------------------------------------

def test_portbundle_queue_sim( dump_vcd ):

  test_vectors = [

    # Enqueue one element and then dequeue it
    # enq_val enq_rdy enq_bits deq_val deq_rdy deq_bits
    [ 1,      1,      0x0001,  0,      1,      '?'    ],
    [ 0,      0,      0x0000,  1,      1,      0x0001 ],
    [ 0,      1,      0x0000,  0,      0,      '?'    ],

    # Fill in the queue and enq/deq at the same time
    # enq_val enq_rdy enq_bits deq_val deq_rdy deq_bits
    [ 1,      1,      0x0002,  0,      0,      '?'    ],
    [ 1,      0,      0x0003,  1,      0,      0x0002 ],
    [ 0,      0,      0x0003,  1,      0,      0x0002 ],
    [ 1,      0,      0x0003,  1,      1,      0x0002 ],
    [ 1,      1,      0x0003,  0,      1,      '?'    ],
    [ 1,      0,      0x0004,  1,      1,      0x0003 ],
    [ 1,      1,      0x0004,  0,      1,      '?'    ],
    [ 0,      0,      0x0004,  1,      1,      0x0004 ],
    [ 0,      1,      0x0004,  0,      1,      '?'    ],

  ]

  # Instantiate and elaborate the model

  model = PortBundleQueue( 16 )
  model.elaborate()

  # Define functions mapping the test vector to ports in model

  def tv_in( model, test_vector ):

    model.enq.val.v = test_vector[0]
    model.enq.msg.v = test_vector[2]
    model.deq.rdy.v = test_vector[4]

  def tv_out( model, test_vector ):

    assert model.enq.rdy.v == test_vector[1]
    assert model.deq.val.v == test_vector[3]
    if not test_vector[5] == '?':
      assert model.deq.msg.v == test_vector[5]

  # Run the test

  sim = new_pmlib.TestVectorSimulator( model, test_vectors, tv_in, tv_out )
  #if dump_vcd:
  #  sim.dump_vcd( "PortBundle_test.vcd" )
  sim.run_test()

#-------------------------------------------------------------------------
# Test Translation
#-------------------------------------------------------------------------
#
#def test_portbundle_queue_translation( ):
#
#    # Create temporary file to write out Verilog
#
#    temp_file = "PortBundle_test.v"
#    compile_cmd = ("iverilog -g2005 -Wall -Wno-sensitivity-entire-vector"
#                    "-Wno-sensitivity-entire-array " + temp_file)
#    fd = open( temp_file, 'w' )
#
#    # Instantiate and elaborate model
#
#    model = PortBundleQueue( 16 )
#    model.elaborate()
#
#    # Translate
#
#    code = VerilogTranslationTool( model, fd )
#    fd.close()
#
#    # Make sure translation compiles
#    # TODO: figure out a way to group PortBundles during translation?
#
#    x = os.system( compile_cmd )
#    assert x == 0
#
