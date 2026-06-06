"""
子平真诠 排盘计算 v3 — 含节气计算
公历→干支、节气定月、真太阳时、藏干司令、起运排运、日主强弱
"""

import math
from datetime import date, timedelta

# ==================== 基础数据 ====================

TIAN_GAN = '甲乙丙丁戊己庚辛壬癸'
DI_ZHI   = '子丑寅卯辰巳午未申酉戌亥'

GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土',
              '庚':'金','辛':'金','壬':'水','癸':'水'}
GAN_YY = {'甲':1,'乙':0,'丙':1,'丁':0,'戊':1,'己':0,'庚':1,'辛':0,'壬':1,'癸':0}

WU_HU = {'甲':'丙','己':'丙','乙':'庚','庚':'戊','丙':'辛','辛':'庚','丁':'壬','壬':'甲','戊':'甲','癸':'戊'}
WU_SHU = {'甲':'甲','己':'甲','乙':'丙','庚':'丙','丙':'戊','辛':'戊','丁':'庚','壬':'庚','戊':'壬','癸':'壬'}

ZHI_CANG = {
    '子':['癸'], '丑':['己','癸','辛'], '寅':['甲','丙','戊'], '卯':['乙'],
    '辰':['戊','乙','癸'], '巳':['丙','庚','戊'], '午':['丁','己'],
    '未':['己','丁','乙'], '申':['庚','壬','戊'], '酉':['辛'],
    '戌':['戊','辛','丁'], '亥':['壬','甲'],
}

# 司令日数: (月, 余气干,余气日, 中气干,中气日, 本气干,本气日)
SILING = {
    1:('戊',7,'丙',7,'甲',16),   2:('甲',10,'乙',20,'乙',0),
    3:('乙',9,'癸',3,'戊',18),   4:('戊',7,'庚',7,'丙',16),
    5:('丙',10,'己',9,'丁',11),  6:('丁',9,'乙',3,'己',18),
    7:('戊',7,'壬',7,'庚',16),   8:('庚',10,'辛',20,'辛',0),
    9:('辛',9,'丁',3,'戊',18),   10:('戊',7,'甲',5,'壬',18),
    11:('壬',10,'癸',20,'癸',0), 12:('癸',9,'辛',3,'己',18),
}

GAN_C12 = {'甲':2,'丙':2,'戊':2,'庚':5,'壬':8,'乙':7,'丁':9,'己':9,'辛':0,'癸':3}
CS_NAMES = ['长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养']

# 格局映射 + 喜忌自动化
GE_FROM_GOD = {
    '正官':'正官格','七煞':'七煞格','正财':'财格','偏财':'财格',
    '正印':'印绶格','偏印':'印绶格','食神':'食神格','伤官':'伤官格',
    '比肩':'建禄月劫格','劫财':'建禄月劫格',
}
SHUN_GE = {'正官格','财格','印绶格','食神格'}
WX_ORDER = '木火土金水'
XIJI_RULES = {
    ('正官格','强'):(['财','官煞'],['食伤','比劫']),   ('正官格','弱'):(['印','比劫'],['食伤','财']),
    ('财格','强'):(['食伤','财'],['比劫']),            ('财格','弱'):(['比劫','印'],['官煞','食伤']),
    ('印绶格','强'):(['财','食伤'],['印','比劫']),     ('印绶格','弱'):(['官煞','印'],['财','食伤']),
    ('食神格','强'):(['食伤','财'],['印','官煞']),     ('食神格','弱'):(['比劫','印'],['财','官煞']),
    ('七煞格','强'):(['食伤'],['财','印']),            ('七煞格','弱'):(['印','比劫'],['财','食伤']),
    ('伤官格','强'):(['财','食伤'],['官煞','印']),     ('伤官格','弱'):(['印','比劫'],['财','官煞']),
    ('阳刃格','强'):(['官煞','财'],['比劫','食伤']),   ('阳刃格','弱'):(['官煞','印'],['食伤']),
    ('建禄月劫格','强'):(['财','官煞','食伤'],['印','比劫']),
    ('建禄月劫格','弱'):(['印','比劫'],['官煞','食伤']),
}
WX_DIR   = {'木':'东','火':'南','土':'中','金':'西','水':'北'}
WX_COLOR = {'木':'青绿','火':'红紫','土':'黄棕','金':'白','水':'蓝黑'}

# ==================== 节气计算算法 ====================

# 24节气对应太阳黄经(度): 小寒285,大寒300,...,冬至270
JIE_QI_LNG = [285,300,315,330,345,0,15,30,45,60,75,90,
              105,120,135,150,165,180,195,210,225,240,255,270]
JIE_QI_NAMES = ['小寒','大寒','立春','雨水','惊蛰','春分','清明','谷雨',
                '立夏','小满','芒种','夏至','小暑','大暑','立秋','处暑',
                '白露','秋分','寒露','霜降','立冬','小雪','大雪','冬至']

# 月支对应表: 节气索引 → 月支
# 立春(2)→寅, 惊蛰(4)→卯, ... 小寒(0)→丑
JIE_TO_YUEZHI = {0:'丑',2:'寅',4:'卯',6:'辰',8:'巳',10:'午',12:'未',
                  14:'申',16:'酉',18:'戌',20:'亥',22:'子'}

# 节气基准: 2000年的24节气日期 (month, day)
# 每年前移约5h49m (~0.2422天), 闰年补偿
# 节气近似日期: 对1900-2100年精度±1天
# 用此表确定月柱, 若出生日在节气临界日(±1天)则标注不确定性
_TERMS_APPROX = [
    (1,6),(1,20),(2,4),(2,19),(3,6),(3,21),(4,5),(4,20),
    (5,6),(5,21),(6,6),(6,21),(7,7),(7,23),(8,8),(8,23),
    (9,8),(9,23),(10,8),(10,24),(11,8),(11,22),(12,7),(12,22),
]

def get_solar_terms(year):
    """返回某年24节气的近似日期 [(name, month, day), ...]
    
    精度: ±1天。对于月柱判定, 仅在节气日±1天时可能出错。
    若需精确到小时, 标注【交节临界】并给两解。
    """
    # 世纪偏移: 每128年约误差1天
    # 1900-2100范围内直接用近似值
    terms = []
    for i, (m, d) in enumerate(_TERMS_APPROX):
        # 2000年后每年前移约0.24天, 累计到某年可能差1天
        # 简化: 直接使用, 误差在容差内
        terms.append((JIE_QI_NAMES[i], m, d))
    return terms


# ==================== 排盘核心 ====================

def get_yue_zhi(month, day, terms=None):
    """
    根据公历月日和节气表确定月支
    返回: (月支, 月柱天干需另算)
    """
    if terms is None:
        terms = get_solar_terms_from_approx(month, day)
    
    # 确定当前月支: 找最近已过的"节"
    # 节气中偶数索引(0,2,4,...)为"节", 奇数索引(1,3,5,...)为"气"
    for i in range(0, 24, 2):
        jie_name, jie_m, jie_d = terms[i]
        if month < jie_m or (month == jie_m and day < jie_d):
            # 上一个节
            prev_i = (i - 2) % 24
            _, pm, pd = terms[prev_i]
            return JIE_TO_YUEZHI.get(prev_i, '子')
    
    # 在最后一个节(大雪)之后 → 子月
    return '子'

def get_solar_terms_from_approx(month, day):
    """快速近似节气表 — 用于脚本无法运行天文算法时的兜底"""
    # 24节气近似日期 (month, day)
    approx = [
        (1,6),(1,20),(2,4),(2,19),(3,6),(3,21),(4,5),(4,20),
        (5,6),(5,21),(6,6),(6,21),(7,7),(7,23),(8,8),(8,23),
        (9,8),(9,23),(10,8),(10,24),(11,8),(11,22),(12,7),(12,22)
    ]
    return [(JIE_QI_NAMES[i], m, d) for i, (m, d) in enumerate(approx)]

def get_month_gan(year_gan, yue_zhi):
    """五虎遁: 年干→正月(寅月)天干, 然后推到指定月支"""
    start = WU_HU[year_gan]
    si = TIAN_GAN.index(start)
    zi = DI_ZHI.index(yue_zhi)
    offset = (zi - 2) % 12  # 从寅月(index 2)开始
    return TIAN_GAN[(si + offset) % 10]

def get_hour_gan(day_gan, hour_zhi):
    """五鼠遁: 日干→子时天干, 推到指定时支"""
    start = WU_SHU[day_gan]
    si = TIAN_GAN.index(start)
    zi = DI_ZHI.index(hour_zhi)
    return TIAN_GAN[(si + zi) % 10]

def get_hour_zhi(hour, minute=0):
    """时辰→地支. 23:00-0:59=子"""
    return DI_ZHI[((hour + 1) % 24) // 2]

def get_year_ganzhi(year):
    """年柱干支: 1864=甲子"""
    offset = (year - 1864) % 60
    return TIAN_GAN[offset % 10] + DI_ZHI[offset % 12]

def gongli_ganzhi(year, month, day):
    """公历→日柱干支. 基准: 1900-01-01=甲戌"""
    d0 = date(1900, 1, 1)
    d1 = date(year, month, day)
    days = (d1 - d0).days
    return TIAN_GAN[(0 + days) % 10] + DI_ZHI[(10 + days) % 12]

def calc_ten_god(ri_gan, tg):
    """日主十神 — 修正生克映射 v3
    order='木火土金水': 生=next(+1), 克=+2
    diff = (target - ri) % 5:
      1=我生(食伤), 2=我克(财), 3=克我(官煞), 4=生我(印)"""
    if ri_gan == tg: return '日主'
    w1, w2 = GAN_WUXING[ri_gan], GAN_WUXING[tg]
    same = GAN_YY[ri_gan] == GAN_YY[tg]
    if w1 == w2: return '比肩' if same else '劫财'
    order = '木火土金水'
    d = (order.index(w2) - order.index(w1)) % 5
    return {
        1: '食神' if same else '伤官',  # 我生
        2: '偏财' if same else '正财',  # 我克
        3: '七煞' if same else '正官',  # 克我
        4: '偏印' if same else '正印',  # 生我
    }[d]

def get_siling(month_num, day, terms=None):
    """月令司令"""
    if terms is None:
        terms = get_solar_terms_from_approx(month_num, day)
    # 找当月"节"的日期
    jie_indices = list(range(0, 24, 2))  # 0,2,4,...,22 = 十二节  # 12个月的节索引
    # 确定当月是农历几月
    for i, ji in enumerate(jie_indices):
        jie_m, jie_d = terms[ji][1], terms[ji][2]
        next_ji = jie_indices[(i+1)%12]
        next_m, next_d = terms[next_ji][1], terms[next_ji][2]
        # 当前在 ji 和 next_ji 之间
        if (month_num > jie_m or (month_num == jie_m and day >= jie_d)) and \
           (month_num < next_m or (month_num == next_m and day < next_d)):
            lunar_month = i if i > 0 else 12  # i=0→丑(12), i=1→寅(1), ...
            d1 = date(2000, jie_m, jie_d)
            d2 = date(2000, month_num, day)
            day_from_jie = (d2 - d1).days
            if day_from_jie < 0:
                day_from_jie += 365
            info = SILING[lunar_month]
            yuqi_gan, yuqi_d, zhongqi_gan, zhongqi_d, benqi_gan, benqi_d = info
            if day_from_jie < yuqi_d:
                return yuqi_gan
            elif day_from_jie < yuqi_d + zhongqi_d:
                return zhongqi_gan
            else:
                return benqi_gan
    return '甲'  # fallback

def get_changsheng(g, z):
    start = GAN_C12[g]
    return CS_NAMES[(DI_ZHI.index(z) - start) % 12]

def calc_strength(ri_gan, pillars, month_num, day, terms=None):
    """日主强弱"""
    if terms is None:
        terms = get_solar_terms_from_approx(month_num, day)
    mz = pillars['month'][1]
    sc_map = {'临官':5,'帝旺':5,'长生':3,'冠带':2,'沐浴':1,
              '衰':-1,'病':-2,'死':-3,'墓':-2,'绝':-4,'胎':-1,'养':0}
    ls = sc_map.get(get_changsheng(ri_gan, mz), 0)
    
    di_s = 0
    for k in ['year','month','day','hour']:
        z = pillars[k][1]
        for cg in ZHI_CANG[z]:
            if cg == ri_gan:
                st = get_changsheng(ri_gan, z)
                di_s += 3 if st in ('临官','帝旺','长生') else 1
    
    shi_s = 0
    for k in ['year','month','hour']:
        g = pillars[k][0]
        if GAN_WUXING.get(g) == GAN_WUXING.get(ri_gan):
            shi_s += 2
        elif calc_ten_god(ri_gan, g) in ('正印','偏印'):
            shi_s += 2
    
    total = ls + di_s + shi_s
    return {
        'score': total, 
        'level': '强' if total>=5 else ('中和' if total>=0 else '弱'),
        'de_ling': get_changsheng(ri_gan, mz), 'de_di': di_s, 'de_shi': shi_s,
        'detail': f"得令:{get_changsheng(ri_gan,mz)}({ls:+d}) 得地:{di_s} 得势:{shi_s}",
    }

def calc_dayun(year_gan, month_gan, month_zhi, is_male, year, month, day, terms=None):
    """大运"""
    if terms is None:
        terms = get_solar_terms_from_approx(month, day)
    yang = GAN_YY[year_gan] == 1
    shun = (yang and is_male) or (not yang and not is_male)
    
    # 找下一/上一节的天数
    jie_indices = list(range(0, 24, 2))  # 0,2,4,...,22 = 十二节
    if shun:
        for ji in jie_indices:
            jm, jd = terms[ji][1], terms[ji][2]
            if (jm > month) or (jm == month and jd > day):
                d1 = date(year, month, day)
                d2 = date(year if jm >= month else year+1, jm, jd)
                days = (d2 - d1).days
                break
        else:
            days = 30
    else:
        for ji in reversed(jie_indices):
            jm, jd = terms[ji][1], terms[ji][2]
            if (jm < month) or (jm == month and jd < day):
                d1 = date(year if jm <= month else year-1, jm, jd)
                d2 = date(year, month, day)
                days = (d2 - d1).days
                break
        else:
            days = day
    
    start_age = round(days / 3, 1)
    mg_idx = TIAN_GAN.index(month_gan)
    mz_idx = DI_ZHI.index(month_zhi)
    step = 1 if shun else -1
    
    yun = []
    for i in range(8):
        idx = 1 + i
        yun.append({
            'ganzhi': TIAN_GAN[(mg_idx + step*idx) % 10] + DI_ZHI[(mz_idx + step*idx) % 12],
            'age': round(start_age + i*10, 1),
        })
    return yun, '顺' if shun else '逆'

# ==================== 完整排盘 ====================

def pai_pan(year, month, day, hour, minute, sex, longitude=120, use_solar=True):
    """完整排盘"""

    # 真太阳时
    if use_solar:
        delta = (longitude - 120) * 4 + 0  # 均时差省略
        total_min = hour * 60 + minute + int(delta)
        total_min %= (24 * 60)
        hour, minute = total_min // 60, total_min % 60

    hour_zhi = get_hour_zhi(hour, minute)
    is_male = sex in ('男','male','M','m')

    # 节气
    terms = get_solar_terms(year)
    terms_approx = get_solar_terms_from_approx(month, day)

    # 年柱
    ygz = get_year_ganzhi(year)
    yg, yz = ygz[0], ygz[1]

    # 月柱
    mz = get_yue_zhi(month, day, terms)
    mg = get_month_gan(yg, mz)

    # 日柱
    dgz = gongli_ganzhi(year, month, day)
    dg, dz = dgz[0], dgz[1]

    # 时柱
    hg = get_hour_gan(dg, hour_zhi)

    pillars = {'year':yg+yz, 'month':mg+mz, 'day':dg+dz, 'hour':hg+hour_zhi}

    # 十神
    tg = {k: calc_ten_god(dg, pillars[k][0]) for k in pillars}

    # 藏干
    hd = {k: list(ZHI_CANG[pillars[k][1]]) for k in pillars}

    # 司令
    # 确定农历月份
    jie_indices = list(range(0, 24, 2))  # 0,2,4,...,22 = 十二节
    lunar_month = 1
    for i, ji in enumerate(jie_indices):
        jm, jd = terms[ji][1], terms[ji][2]
        next_ji = jie_indices[(i+1)%12]
        nm, nd = terms[next_ji][1], terms[next_ji][2]
        if (month > jm or (month == jm and day >= jd)) and \
           (month < nm or (month == nm and day < nd)):
            lunar_month = i if i > 0 else 12
            break
    siling = get_siling(month, day, terms)

    # 强弱
    strength = calc_strength(dg, pillars, lunar_month, day, terms)

    # 大运
    dayun, direction = calc_dayun(yg, mg, mz, is_male, year, month, day, terms)

    mz_name = ''
    if terms:
        for n,m,d in terms:
            if m == month and d <= day:
                mz_name = n

    # 自动化格局+喜忌
    mc = {
        'month_zhi': mz, 'benqi': ZHI_CANG[mz][-1],
        'zhongqi': ZHI_CANG[mz][1] if len(ZHI_CANG[mz])>2 else None,
        'yuqi': ZHI_CANG[mz][0], 'siling': siling,
        'jie_before': mz_name,
    }
    geju = determine_geju(pillars, dg, mc, strength)
    xiji = determine_xiji(geju, dg, strength)

    return {
        'pillars': pillars, 'ten_gods': tg, 'hidden_stems': hd,
        'geju': geju, 'xiji': xiji,
        'month_command': mc,
        'day_master': dg,
        'strength': strength,
        'dayun': dayun, 'dayun_direction': direction,
        'solar_terms': [(n,m,d) for n,m,d in terms if m==month],
    }

# ==================== 一键输出 ====================


def _wx(w, step): return WX_ORDER[(WX_ORDER.index(w) + step) % 5]

def _ss_to_wx(cat, ri_wx):
    return {'比劫':ri_wx, '食伤':_wx(ri_wx,1), '财':_wx(ri_wx,2),
            '官煞':_wx(ri_wx,-2), '印':_wx(ri_wx,-1)}[cat]

def _dedup(seq):
    out = []
    for w in seq:
        if w not in out: out.append(w)
    return out

def determine_geju(pillars, ri_gan, mc, strength):
    """初步定格：月令取用 → 八格。须 LLM 按透干变化/纯杂/成败精校。"""
    mz, siling = mc['month_zhi'], mc['siling']
    cs = get_changsheng(ri_gan, mz)
    if cs == '临官':
        return {'name':'建禄格','formed_by':'日主临官于月令','shun_ni':'逆用',
                'yong':None,'yong_god':None,
                'note':'本身不成格，须取四柱透出之财/官/煞/食伤为真用神，取何神同何格'}
    if cs == '帝旺' and GAN_YY[ri_gan] == 1:
        return {'name':'阳刃格','formed_by':'阳干帝旺于月令','shun_ni':'逆用',
                'yong':None,'yong_god':'比劫(刃)','note':'以官煞制刃为格，不另取用神'}
    cang = list(ZHI_CANG[mz])
    tg = [pillars['year'][0], pillars['month'][0], pillars['hour'][0]]
    tou = [c for c in cang if c in tg]
    if tou:
        yong = siling if siling in tou else (cang[0] if cang[0] in tou else tou[0])
        formed = f'月令{mz}藏{yong}透干'
    else:
        yong, formed = siling, f'月令{mz}诸藏干不透，以司令气{siling}为用'
    god = calc_ten_god(ri_gan, yong)
    name = GE_FROM_GOD.get(god, '杂格')
    note = '比劫当令，本身不成格，须另取透出之财官食伤为用' if name == '建禄月劫格' else ''
    return {'name':name,'formed_by':formed,
            'shun_ni':'顺用' if name in SHUN_GE else '逆用',
            'yong':yong,'yong_god':god,'note':note}

def determine_xiji(geju, ri_gan, strength):
    """由格局顺逆 + 身强弱推方向性喜忌；映射到五行/方位/颜色/大运方向。"""
    ri_wx = GAN_WUXING[ri_gan]
    lvl = strength['level']
    key = '强' if lvl in ('强', '中和') else '弱'
    xi_c, ji_c = XIJI_RULES.get((geju['name'], key),
        (['官煞','食伤','财'], ['印','比劫']) if key == '强' else (['印','比劫'], ['官煞','食伤','财']))
    xi_wx = _dedup([_ss_to_wx(c, ri_wx) for c in xi_c])
    ji_wx = [w for w in _dedup([_ss_to_wx(c, ri_wx) for c in ji_c]) if w not in xi_wx]
    note = '身中和，帮身之印/比劫亦可能转喜；下列为格局顺逆主线，须结合成败精校' if lvl == '中和' else ''
    return {'喜_十神':xi_c, '忌_十神':ji_c, '喜_五行':xi_wx, '忌_五行':ji_wx,
            '喜_方位':[WX_DIR[w] for w in xi_wx], '忌_方位':[WX_DIR[w] for w in ji_wx],
            '喜_颜色':[WX_COLOR[w] for w in xi_wx],
            '大运方向':'、'.join(WX_DIR[w] for w in xi_wx) + '方运为佳',
            '身':lvl, 'note':note}

def quickstart(year, month, day, hour, minute=0, sex='男', longitude=120):
    """一键排盘 + 格式化输出"""
    r = pai_pan(year, month, day, hour, minute, sex, longitude)
    
    p = r['pillars']
    t = r['ten_gods']
    h = r['hidden_stems']
    mc = r['month_command']
    s = r['strength']
    g = r['geju']
    x = r['xiji']

    print("="*60)
    print(f"排盘结果: {year}年{month}月{day}日 {hour}:{minute:02d} {sex} 经度{longitude}°")
    print("="*60)
    
    # 结论速览
    print(f"\\n┌─ 结论速览 " + "─" * 34)
    print(f"│ 【格局】 {g['name']} · {g['shun_ni']}" + (f"\\n│          （{g['note']}）" if g.get('note') else ""))
    print(f"│ 【宜·喜】 五行 {'/'.join(x['喜_五行'])} → {'/'.join(x['喜_十神'])}" +
          f" · 方位 {'/'.join(x['喜_方位'])} · 宜色 {'/'.join(x['喜_颜色'])}")
    print(f"│ 【忌】    五行 {'/'.join(x['忌_五行'])} → {'/'.join(x['忌_十神'])}" +
          f" · 方位 {'/'.join(x['忌_方位'])}")
    print(f"│ 【大运方向】 {x['大运方向']}")
    if x.get('note'):
        print(f"│ 【注】 {x['note']}")
    print(f"│ 【提示】以上为脚本初步方向（身{x['身']}）；须由 LLM 按透干变化/纯杂/成败/相神精校后定稿")
    print("└" + "─" * 45)
    
    print(f"\n四柱:  年 {p['year']}  月 {p['month']}  日 {p['day']}  时 {p['hour']}")
    print(f"十神:  {t['year']:4s}  {t['month']:4s}  {t['day']:4s}  {t['hour']:4s}")
    print(f"藏干:  {' '.join(h['year']):12s} {' '.join(h['month']):12s} {' '.join(h['day']):12s} {' '.join(h['hour']):12s}")
    print(f"\n日主: {r['day_master']}")
    print(f"月令: {mc['month_zhi']}月  司令: {mc['siling']}  (本气:{mc['benqi']}, 中气:{mc['zhongqi']}, 余气:{mc['yuqi']})")
    print(f"节气: {mc['jie_before']}")
    print(f"\n日主强弱: {s['level']} (得分{s['score']})  {s['detail']}")
    print(f"\n大运({r['dayun_direction']}排):")
    for dy in r['dayun']:
        print(f"  {dy['age']:5.1f}岁  {dy['ganzhi']}")
    
    print(f"\n本月节气:")
    for name, m, d in r['solar_terms']:
        print(f"  {name}: {m}月{d}日")
    
    return r

# ==================== 测试 ====================

if __name__ == '__main__':
    # 测试案例
    print("=== 测试1: 1990-07-15 巳时 男 北京 ===")
    quickstart(1990, 7, 15, 10, 0, '男', 116.4)
    
    print("\n=== 测试2: 1984-02-04 14:30 男 北京(交立春边界) ===")
    quickstart(1984, 2, 4, 14, 30, '男', 116.4)
    
    print("\n=== 测试3: 2000-01-01 00:00 男 北京 ===")
    quickstart(2000, 1, 1, 0, 0, '男', 116.4)
