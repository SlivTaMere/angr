#!/usr/bin/env python

import nose
import logging
import angr
import os

test_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../binaries/tests'))

def prepare_mipsel():
    ping = os.path.join(test_location, "mipsel/darpa_ping")
    skip=['libgcc_s.so.1', 'libresolv.so.0']
    load_options={'skip_libs': skip}
    p = angr.Project(ping, load_options=load_options)
    return p

def prepare_ppc():
    libc = os.path.join(test_location, "ppc/libc.so.6")
    p = angr.Project(libc, load_options={'auto_load_libs':True})
    return p

def test_ppc():
    p = prepare_ppc()
    # This tests the relocation of _rtld_global_ro in ppc libc6.
    # This relocation is of type 20, and relocates a non-local symbol
    relocated = p.ld.memory.read_addr_at(0x18ace4)
    nose.tools.assert_equal(relocated % 0x1000, 0xf666e320 % 0x1000)

def test_mipsel():
    p = prepare_mipsel()
    dep = p.ld._satisfied_deps
    loadedlibs = set(p.ld.shared_objects.keys())

    # 1) check dependencies and loaded binaries
    nose.tools.assert_true(dep.issuperset({'libresolv.so.0', 'libgcc_s.so.1', 'libc.so.6', 'ld.so.1'}))
    nose.tools.assert_equal(loadedlibs, {'libc.so.6', 'ld.so.1'})

    # cfg = p.construct_cfg()
    # nodes = cfg.get_nodes()

    # Get the address of simprocedure __uClibc_main
    sproc_addr = 0
    s_name = "<class 'simuvex.procedures.libc___so___6.__uClibc_main.__uClibc_main'>"
    for k,v in p.sim_procedures.iteritems():
        if str(v[0]) == s_name:
            sproc_addr = k
    nose.tools.assert_false(sproc_addr == 0)

    # 2) Check GOT slot containts the right address
    # Cle: 4494036
    got = p.ld.find_symbol_got_entry('__uClibc_main')
    addr = p.ld.memory.read_addr_at(got)
    nose.tools.assert_equal(addr, sproc_addr)

    ioctl = p.ld.find_symbol_got_entry("ioctl")
    setsockopt = p.ld.find_symbol_got_entry("setsockopt")

    nose.tools.assert_equal(ioctl, 4494300)
    nose.tools.assert_equal(setsockopt, 4494112)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_mipsel()
    test_ppc()
