from datetime import datetime, timedelta
import math

def get_last_week_range(today=None):
    """
    오늘(보통 월요일) 기준으로 지난주 월요일~일요일 날짜 범위를 반환
    Returns: (start_date_obj, end_date_obj)
    """
    if today is None:
        today = datetime.now()
    
    # 오늘이 월요일(0)이라고 가정하고 지난주 월요일은 7일 전
    # 발송일(월요일) 기준 지난주 월~일 데이터 수집
    days_since_monday = today.weekday() # 월=0, 화=1, ...
    
    # 지난주 일요일 = 오늘 - (오늘요일 + 1)
    # 예: 오늘이 월(0) -> -1일(어제)
    last_sunday = today - timedelta(days=days_since_monday + 1)
    
    # 지난주 월요일 = 지난주 일요일 - 6일
    last_monday = last_sunday - timedelta(days=6)
    
    return last_monday, last_sunday

def get_week_number(date_obj):
    """
    해당 날짜가 그 달의 몇 번째 주인지 계산 (ISO 기준 아님, 통상적 달력 기준)
    매월 1일이 있는 주를 1주차로 간주
    """
    first_day = date_obj.replace(day=1)
    
    # 1일의 요일 (월=0, ... 일=6)
    first_weekday = first_day.weekday()
    
    # 해당 날짜가 1일부터 며칠 떨어져 있는지
    days_from_first = date_obj.day - 1
    
    # 1일이 속한 주의 시작(월요일)부터의 오프셋
    # (first_weekday + days_from_first) // 7
    # 예: 1일이 수요일(2)이고, 2일(목)인 경우 -> (2+1)//7 = 0 -> 1주차
    # 예: 1일이 일요일(6)이고, 2일(월)인 경우 -> (6+1)//7 = 1 -> 2주차 (월요일 시작 기준이므로)
    
    return ((first_weekday + days_from_first) // 7) + 1

def get_newsletter_title_date(today=None):
    """
    뉴스레터 제목용 날짜 문자열 생성 (예: 12월 3주차)
    기준: 지난주 데이터를 다루므로, '지난주'가 몇 월 몇 주차인지, 
    혹은 '이번주' 발송분인지 정책 결정 필요.
    보통 '12월 3주차 뉴스레터'라고 하면 3주차에 발송되는(2주차 내용을 담은) 것을 의미하거나,
    2주차 내용을 담은 것을 2주차 뉴스레터라고 하기도 함.
    
    여기서는 '발송일 기준' 주차를 사용.
    """
    if today is None:
        today = datetime.now()
        
    month = today.month
    week_num = get_week_number(today)
    
    return f"{month}월 {week_num}주차"

def get_date_range_str(start_date, end_date):
    """
    날짜 범위 문자열 (예: 12.15 ~ 12.21)
    """
    return f"{start_date.strftime('%m.%d')} ~ {end_date.strftime('%m.%d')}"

def get_last_month_range(today=None):
    """
    오늘 기준으로 지난달 1일~말일 날짜 범위를 반환
    Returns: (start_date_obj, end_date_obj)
    """
    if today is None:
        today = datetime.now()
        
    # 이번달 1일
    this_month_first = today.replace(day=1)
    
    # 지난달 말일 = 이번달 1일 - 1일
    last_month_end = this_month_first - timedelta(days=1)
    
    # 지난달 1일
    last_month_start = last_month_end.replace(day=1)
    
    return last_month_start, last_month_end

def is_business_day(date_obj):
    """
    영업일 여부 확인 (주말 제외, 공휴일은 별도 라이브러리 없으면 단순 주말 체크)
    월=0, ... 금=4, 토=5, 일=6
    """
    return date_obj.weekday() < 5

def get_first_business_day(year, month):
    """
    해당 월의 첫 번째 영업일 반환
    """
    date = datetime(year, month, 1)
    while not is_business_day(date):
        date += timedelta(days=1)
    return date
