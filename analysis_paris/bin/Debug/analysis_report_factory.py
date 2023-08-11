# -----------------------------------------------------------
# 파이썬으로 GIF 또는 맵 구현하는 파이썬 파일입니다.
# 작성자 : 송민정
# 작성일자 : 2023-08-08
# 명령어 예시 :
#       ex)
# 예상 리턴은 관련 함수를 검색바랍니다.
# -----------------------------------------------------------
import random
import sys

import common

from Class.FTP import *
from Class.Graph import Graph
from Class.KakaoMap import KakaoMap


class ReportMethod:
    ## 함수 이름을 str로 저장해서 씁니다. (오탈자 예방용) calling_method_name_list ##
    get_selling_area_report = 'get_selling_area_report'
    get_location_report = 'get_location_report'


def main():
    calling_method_name, other_parameters = common.split_system_argument_values(sys.argv)
    factory = MapFactory()
    mode_option = ""

    # 가맹점 조회
    if calling_method_name == ReportMethod.get_selling_area_report:
        # ========== 가맹점/매물정보 분기점 만들기
        domain_id = int(other_parameters[0])
        table_type = other_parameters[1]
        factory.get_selling_area_report(domain_id, table_type)
        mode_option = table_type
        # print(f"메소드 {ReportMethod.get_selling_area_report} 호출됨. 전달된 가맹점 아이디 : {selling_area_id}")

    elif calling_method_name == ReportMethod.get_location_report:
        latitude, longitude = map(float, other_parameters[0], other_parameters[1])
        factory.get_location_report(latitude, longitude)
        mode_option = "location"
        # print(f"메소드 {ReportMethod.get_location_report} 호출됨. 전달된 위도 : {latitude},  경도 : {longitude}")

    factory.get_graph(mode_option)  # 어떤 함수가 호출되든 그래프를 그려줍니다


class MapFactory:

    def __init__(self):
        self.result = None
        self.ftp = FTP()
        self.ftp.connect()
        from db_connector import DBConnector
        from python_controller import Path
        self.conn = DBConnector(test_option=True, config_path=Path().CONFIG_PATH)
        self.file_path = Path().db_connector_path[:-15]

    def get_selling_area_report(self, domain_id, table_type):
        is_paris = False
        # 검색 결과 가져오기
        if table_type == "selling_area":
            selling_area_id = domain_id
            self.result = self.conn.get_selling_area_by_id(selling_area_id)
        elif table_type == "paris":
            is_paris = True
            paris_id = domain_id
            self.result = self.conn.find_paris_by_id(paris_id)  # paris 는 address column 이름 수정 필요
            self.result.rename(columns={"PARIS_ADDRESS": "ADDRESS"}, inplace=True)

        # ----- 지도 생성&업로드
        kakao_map = KakaoMap()

        kakao_map.set_map_info(self.result["LATITUDE"][0], self.result["LONGITUDE"][0], level=3,
                               title=self.result["ADDRESS"][0])
        kakao_map.set_control_view(True)

        # ===== 파리바게뜨 로고로 마커 출력하기
        if is_paris is True:
            kakao_map.set_marker_custom(True)

        file_path = self.file_path + r"\Map\test_map2.html"

        kakao_map.save_map(file_path)
        self.ftp.save_file(file_path)

    def get_location_report(self, latitude, longitude):
        # 검색 결과 가져오기

        # ===== 좌표 검색 DB 함수 추가하기
        # self.result 값만 교체 해주면 됩니다.
        # self.result = self.conn.get_selling_area_by_id(selling_area_id)
        pass

    @staticmethod
    def generate_random_colors(n):
        colors = []
        for _ in range(n):
            random_color = "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
            colors.append(random_color)
        return colors

    def get_graph(self, mode_option):
        # todo : 소득 또는 인구를 꺾은선..?
        if mode_option == "paris":
            model1 = self.conn.get_paris_avg()  # 전체 평균
            model2 = self.conn.get_paris_top_10_avg()  # 상위 10% 평균
        else:  # selling area 또는 location일 경우
            model1 = self.conn.get_selling_area_avg()  # 전체 평균
            model2 = self.conn.get_selling_area_top_10_avg()  # 상위 10% 평균

        # ----- 그래프 생성&업로드
        graph = Graph(700, 500)
        if mode_option == "paris":
            self.result.at[0, 'PARIS_ID'] = self.result.at[0, 'PARIS_NAME']
            model1.at[0, 'PARIS_ID'] = "전체 평균"
            model2.at[0, 'PARIS_ID'] = "상위 10% 평균"
        else:
            self.result.at[0, 'SELLING_AREA_ID'] = self.result.at[0, 'ADDRESS']
            model1.at[0, 'SELLING_AREA_ID'] = "전체 평균"
            model2.at[0, 'SELLING_AREA_ID'] = "상위 10% 평균"

        # ========== 그래프데이터 수정하는곳!!
        # graph.set_data([비교대상 df 3개][출력할 컬럼명])
        # df는 원하는 출력순으로 넣어주시면 됩니다.
        # 출력할 컬럼명에 상호 이름(해당 장소를 구분할수 있는 이름)이 와야합니다. 데이터가 dict 형식으로 저장되있습니다.
        graph.set_ticks(['학교_500',
                         '학교_1000',
                         '학원_500',
                         '학원_1000',
                         '버스정거장_500',
                         '버스정거장_1000',
                         '여가시설_500',
                         '여가시설_1000'])
        if mode_option == 'paris':
            graph.set_data([self.result, model1, model2],
                           ['PARIS_ID',
                            'SCHOOL_COUNT_NEAR_500',
                            'SCHOOL_COUNT_NEAR_1000',
                            'ACADEMY_COUNT_NEAR_500',
                            'ACADEMY_COUNT_NEAR_1000',
                            'STOP_COUNT_NEAR_500',
                            'STOP_COUNT_NEAR_1000',
                            'LEISURE_COUNT_NEAR_500',
                            'LEISURE_COUNT_NEAR_1000', ])

            # DAILY_FLOATING_POPULATION
            # LIVING_POPULATION
            # LIVING_WORKER_AVG_REVENUE
            # LIVING_POPULATION_AVG_REVENUE
        else:
            graph.set_data([self.result, model1, model2],
                           ['SELLING_AREA_ID',
                            'SCHOOL_COUNT_NEAR_500',
                            'SCHOOL_COUNT_NEAR_1000',
                            'ACADEMY_COUNT_NEAR_500',
                            'ACADEMY_COUNT_NEAR_1000',
                            'STOP_COUNT_NEAR_500',
                            'STOP_COUNT_NEAR_1000',
                            'LEISURE_COUNT_NEAR_500',
                            'LEISURE_COUNT_NEAR_1000', ])
        file_path = self.file_path + r"\Graph\test_bar.gif"
        graph.set_color(self.generate_random_colors(8))
        graph.save_gif(file_path)
        self.ftp.save_file(file_path)

        # data = {
        #     '유동인구': int(self.result['DAILY_FLOATING_POPULATION'][0]/10000),
        #     '거주 인구': int(self.result['LIVING_POPULATION'][0]/10000),
        #     '근로자 평균 임금': int(self.result['LIVING_WORKER_AVG_REVENUE'][0]/1000000),
        #     '거주자 평균 임금': int(self.result['LIVING_POPULATION_AVG_REVENUE'][0]/1000000),
        #     '버스정거장_500': int(self.result['STOP_COUNT_NEAR_500'][0]),
        #     '버스정거장_1000': int(self.result['STOP_COUNT_NEAR_1000'][0]),
        #     '여가시설_500': int(self.result['LEISURE_COUNT_NEAR_500'][0]),
        #     '여가시설_1000': int(self.result['LEISURE_COUNT_NEAR_1000'][0]),
        # }
        # graph = Graph(700, 500, "pie")
        # # graph.set_color(['silver', 'gold', 'whitesmoke', 'lightgray', 'blue', 'red', 'green', 'purple'])
        # # graph.set_color(['silver', 'gold', 'whitesmoke', 'lightgray'])
        # graph.set_color(self.generate_random_colors(8))
        # graph.set_data(data)
        #
        # file_path = self.file_path + r"\Graph\test_pie.gif"
        # graph.save_gif(file_path)
        # self.ftp.save_file(file_path)
        # self.ftp.disconnect()


if __name__ == '__main__':
    main()
    # factory = MapFactory()
    # factory.result = factory.conn.get_selling_area_by_id(11)
    # factory.get_graph('not_paris')
