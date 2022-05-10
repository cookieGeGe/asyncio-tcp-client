# -*- coding: utf-8 -*- 
# @Time : 2019/7/17 14:45 
# @Author :  
# @Site :  
# @File : feature_calc.py 
# @Software: PyCharm

async def discharge_type(data, warngingvalue, arg1=40, arg2=48, arg3=6, arg4=15, arg5=30, local_typejudevalue=20):
    local_threshold = warngingvalue
    y_t = [0] * 64  # 存64个相位的放电频次
    phase_list = [[] for i in range(50)]  # 存每个周期对应的放电相位
    isothers = False
    for i in range(64):
        for j in range(50):
            if data[j][i] > local_threshold:
                isothers = True
                y_t[i] += 1
            # if data[j][i] >= local_typejudevalue:
                phase_list[j].append(i)

    # 四个象限: I:0-15 II:16-31 III:32-47 IV:48-63
    iq, iiq, iiiq, ivq = 0, 0, 0, 0
    for i in range(50):
        j = phase_list[i].__len__()
        while j:
            j -= 1
            if 0 <= phase_list[i][j] < 16:
                iq += 1
            elif phase_list[i][j] < 32:
                iiq += 1
            elif phase_list[i][j] < 48:
                iiiq += 1
            else:
                ivq += 1
    # discharge type
    iaxx, iiaxx, vaxx, faxx, paxx, caxx, oaxx = 0, 0, 0, 0, 0, 0, 0
    for i in range(50):
        if len(phase_list[i]) == 0:
            pass
        elif len(phase_list[i]) == 1:
            if iq > arg1 or iiq > arg1 or iiiq > arg1 or ivq > arg1:
                iaxx += 1
            else:
                paxx += 1
        elif len(phase_list[i]) == 2:
            if (iq > arg2 and iiiq > arg2) or (iiq > arg2 and ivq > arg2):
                iiaxx += 1
        elif len(phase_list[i]) < arg3:
            if iq > 30:
                vaxx += 1
            else:
                paxx += 1
        elif len(phase_list[i]) < arg4:
            faxx += 1
        elif len(phase_list[i]) < arg5:
            caxx += 1
        else:
            oaxx += 1
    maxvalue = 0
    dischargetype = ''
    if maxvalue < iaxx and iaxx > 40:
        maxvalue = iaxx
        # dischargetype = 'One line'
        dischargetype = '3'
    if maxvalue < iiaxx:
        maxvalue = iiaxx
        # dischargetype = 'Two line--悬浮放电'
        dischargetype = '8'
    if maxvalue < vaxx:
        maxvalue = vaxx
        # dischargetype = 'Void--空穴放电'
        dischargetype = '4'
    if maxvalue < paxx:
        maxvalue = paxx
        # dischargetype = 'Particle--自由金属颗粒放电'
        dischargetype = '5'
    if maxvalue < faxx:
        maxvalue = faxx
        # dischargetype = 'Floating--悬浮电位放电'
        dischargetype = '2'
    if maxvalue < caxx:
        maxvalue = caxx
        # dischargetype = 'Corona--电晕放电'
        dischargetype = '1'
    if maxvalue < oaxx:
        maxvalue = oaxx
        # dischargetype = 'Offset--环境补偿'
        dischargetype = '6'
    if maxvalue == 0:
        # dischargetype = 'Others--其他放电'
        dischargetype = '7'
    if not isothers:
        # dischargetype = 'None--正常'
        dischargetype = '0'
    return dischargetype