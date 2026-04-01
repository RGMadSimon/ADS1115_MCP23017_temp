
def f1():
    print(1)
    return False

def f2():
    print(2)
    return True

def f3():
    print(3)
    return True

def f4():
    print(4)
    return True

if not f1():
    pass
elif not f2():
    pass
elif not f3():
    pass
elif not f4():
    pass
