#=======================================================================
# arbiters.py
#=======================================================================
'''Collection of arbiter implementations based on vc-Arbiters.'''

from pymtl     import *
from pclib.rtl import Mux, RegEnRst

#-----------------------------------------------------------------------
# RoundRobinArbiter
#-----------------------------------------------------------------------
class RoundRobinArbiter( Model ):

  def __init__( s, nreqs ):

    nreqsX2  = nreqs * 2

    s.reqs   = InPort ( nreqs )
    s.grants = OutPort( nreqs )

    # priority enable

    s.priority_en = Wire( 1 )

    # priority register

    s.priority_reg = m = RegEnRst( nreqs, reset_value = 1 )

    s.connect_dict({
      m.en           : s.priority_en,
      m.in_[1:nreqs] : s.grants[0:nreqs-1],
      m.in_[0]       : s.grants[nreqs-1]
    })

    s.kills        = Wire( 2*nreqs + 1 )
    s.priority_int = Wire( 2*nreqs )
    s.reqs_int     = Wire( 2*nreqs )
    s.grants_int   = Wire( 2*nreqs )

    #-------------------------------------------------------------------
    # comb
    #-------------------------------------------------------------------
    @s.combinational
    def comb():

      s.kills[0].value = 1

      s.priority_int[    0:nreqs  ].value = s.priority_reg.out
      s.priority_int[nreqs:nreqsX2].value = 0
      s.reqs_int    [    0:nreqs  ].value = s.reqs
      s.reqs_int    [nreqs:nreqsX2].value = s.reqs

      # Calculate the kill chain
      for i in range( nreqsX2 ):

        # Set internal grants
        if s.priority_int[i].value:
          s.grants_int[i].value = s.reqs_int[i]
        else:
          s.grants_int[i].value = ~s.kills[i] & s.reqs_int[i]

        # Set kill signals
        if s.priority_int[i].value:
          s.kills[i+1].value = s.grants_int[i]
        else:
          s.kills[i+1].value = s.kills[i] | s.grants_int[i]

      # Assign the output ports
      for i in range( nreqs ):
        s.grants[i].value = s.grants_int[i] | s.grants_int[nreqs+i]

      # Set the priority enable
      s.priority_en.value = ( s.grants != 0 )

  def line_trace( s ):
    return "{} | {}".format( s.reqs, s.grants )

#-----------------------------------------------------------------------
# RoundRobinArbiterEn
#-----------------------------------------------------------------------
class RoundRobinArbiterEn( Model ):
  '''Round Robin Arbiter model with an enable bit.

  Only when 1) the arbiter enable bit is set high AND 2) there is some
  valid arbitration, the priority register is updated. This breaks the
  val-rdy dependency.
  '''
  def __init__( s, nreqs ):

    nreqsX2  = nreqs * 2

    s.en     = InPort ( 1 )
    s.reqs   = InPort ( nreqs )
    s.grants = OutPort( nreqs )

    # priority enable

    s.priority_en = Wire( 1 )

    # priority register

    s.priority_reg = m = RegEnRst( nreqs, reset_value = 1 )

    s.connect_dict({
      m.en           : s.priority_en,
      m.in_[1:nreqs] : s.grants[0:nreqs-1],
      m.in_[0]       : s.grants[nreqs-1]
    })

    s.kills        = Wire( 2*nreqs + 1 )
    s.priority_int = Wire( 2*nreqs )
    s.reqs_int     = Wire( 2*nreqs )
    s.grants_int   = Wire( 2*nreqs )

    #-------------------------------------------------------------------
    # comb_arbitrate
    #-------------------------------------------------------------------

    @s.combinational
    def comb_arbitrate():

      s.kills[0].value = 1

      s.priority_int[    0:nreqs  ].value = s.priority_reg.out
      s.priority_int[nreqs:nreqsX2].value = 0
      s.reqs_int    [    0:nreqs  ].value = s.reqs
      s.reqs_int    [nreqs:nreqsX2].value = s.reqs

      # Calculate the kill chain
      for i in range( nreqsX2 ):

        # Set internal grants
        if s.priority_int[i].value:
          s.grants_int[i].value = s.reqs_int[i]
        else:
          s.grants_int[i].value = ~s.kills[i] & s.reqs_int[i]

        # Set kill signals
        if s.priority_int[i].value:
          s.kills[i+1].value = s.grants_int[i]
        else:
          s.kills[i+1].value = s.kills[i] | s.grants_int[i]

      # Assign the output ports
      for i in range( nreqs ):
        s.grants[i].value = s.grants_int[i] | s.grants_int[nreqs+i]

    #-------------------------------------------------------------------
    # comb_feedback
    #-------------------------------------------------------------------

    @s.combinational
    def comb_feedback():
      s.priority_en.value = ( s.grants != 0 ) & s.en

  def line_trace( s ):
    return "{} | {}".format( s.reqs, s.grants )
