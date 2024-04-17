from libdebug import debugger

d = debugger("/bin/ls")

d.run()

# def callback(d, _):
#     print(hex(d.zmm0))
#     print(hex(d.zmm1))
#     print(hex(d.zmm2))
#     print(hex(d.zmm3))
#     print(hex(d.zmm4))
#     print(hex(d.zmm5))
#     print(hex(d.zmm6))
#     print(hex(d.zmm7))
#     print(hex(d.zmm8))
#     print(hex(d.zmm9))
#     print(hex(d.zmm10))
#     print(hex(d.zmm11))
#     print(hex(d.zmm12))
#     print(hex(d.zmm13))
#     print(hex(d.zmm14))
#     print(hex(d.zmm15))
#     print(hex(d.zmm16))
#     print(hex(d.zmm17))
#     print(hex(d.zmm18))
#     print(hex(d.zmm19))
#     print(hex(d.zmm20))
#     print(hex(d.zmm21))
#     print(hex(d.zmm22))
#     print(hex(d.zmm23))
#     print(hex(d.zmm24))
#     print(hex(d.zmm25))
#     print(hex(d.zmm26))
#     print(hex(d.zmm27))
#     print(hex(d.zmm28))
#     print(hex(d.zmm29))
#     print(hex(d.zmm30))
#     print(hex(d.zmm31))

def callback(d, _):
    # print(hex(d.rip))
    print(hex(d.ymm0))
    print(hex(d.ymm1))
    print(hex(d.ymm2))
    print(hex(d.ymm3))
    print(hex(d.ymm4))
    print(hex(d.ymm5))
    print(hex(d.ymm6))
    print(hex(d.ymm7))
    print(hex(d.ymm8))
    print(hex(d.ymm9))
    print(hex(d.ymm10))
    print(hex(d.ymm11))
    print(hex(d.ymm12))
    print(hex(d.ymm13))
    print(hex(d.ymm14))
    print(hex(d.ymm15))


d.breakpoint(0x4ec5, callback=callback)
# d.breakpoint(0x4ec5)


d.cont()

# d.migrate_to_gdb()

d.kill()
