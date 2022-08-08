with open("./content.txt", "r") as sdTools:
    tools = sdTools.readlines()
    tools = [line.rstrip() for line in tools]
    tab_sum = [0]*3

    for line in tools :
        tab_read = line.split(",")
        if tab_read[1] == 0:
            tab_sum[0] += int(tab_read[0])

    print(tab_sum)

