import json
import os
from datetime import datetime
import logging
import sys # Added for sys.executable

class KeywordManager:
    def __init__(self, config_file=None):
        # exe 파일 실행 시 루트 폴더의 설정 파일을 우선적으로 찾기
        if config_file is None:
            # 현재 실행 파일의 위치 확인
            if getattr(sys, 'frozen', False):
                # exe 파일로 실행된 경우
                exe_dir = os.path.dirname(sys.executable)
                # 루트 폴더의 keywords_config.json 찾기 (상위 폴더로 이동)
                root_config = os.path.join(os.path.dirname(exe_dir), 'keywords_config.json')
                if os.path.exists(root_config):
                    self.config_file = root_config
                    self.logger.info(f"루트 폴더 설정 파일 사용: {root_config}")
                else:
                    # 루트 폴더에 없으면 현재 폴더 사용
                    self.config_file = "keywords_config.json"
                    self.logger.info("현재 폴더 설정 파일 사용")
            else:
                # Python 스크립트로 실행된 경우
                self.config_file = "keywords_config.json"
        else:
            self.config_file = config_file
        
        self.setup_logging()
        self.load_keywords()
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_keywords(self):
        """키워드 설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.keywords_config = json.load(f)
                self.logger.info(f"키워드 설정 파일 로드 완료: {self.config_file}")
            else:
                # 기본 설정 생성
                self.keywords_config = {
                    "topics": [
                        {
                            "name": "여행",
                            "keywords": ["하나투어", "모두투어", "마이리얼트립"],
                            "weight": 100
                        }
                    ],
                    "max_articles_per_topic": 10,
                    "max_topics": 5,
                    "last_updated": datetime.now().isoformat()
                }
                self.save_keywords()
                self.logger.info("기본 키워드 설정 생성 완료")
        
        except Exception as e:
            self.logger.error(f"키워드 설정 로드 중 오류: {e}")
            # 오류 발생 시 기본 설정으로 초기화
            self.keywords_config = {
                "topics": [
                    {
                        "name": "여행",
                        "keywords": ["하나투어", "모두투어", "마이리얼트립"],
                        "weight": 100
                    }
                ],
                "max_articles_per_topic": 10,
                "max_topics": 5,
                "last_updated": datetime.now().isoformat()
            }
            # 기본 설정으로 파일 재생성
            try:
                self.save_keywords()
                self.logger.info("기본 설정으로 파일 재생성 완료")
            except Exception as save_error:
                self.logger.error(f"기본 설정 저장 중 오류: {save_error}")
    
    def save_keywords(self):
        """키워드 설정 파일 저장"""
        try:
            self.keywords_config["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.keywords_config, f, ensure_ascii=False, indent=2)
            self.logger.info("키워드 설정 파일 저장 완료")
            return True
        except Exception as e:
            self.logger.error(f"키워드 설정 저장 중 오류: {e}")
            return False
    
    def add_topic(self, name, keywords, weight=20):
        """새로운 주제 추가"""
        try:
            # 최대 주제 수 확인
            if len(self.keywords_config["topics"]) >= self.keywords_config["max_topics"]:
                self.logger.warning(f"최대 주제 수({self.keywords_config['max_topics']})에 도달했습니다.")
                return False
            
            # 키워드 수 제한 확인
            if len(keywords) > 10:
                keywords = keywords[:10]
                self.logger.warning("키워드가 10개로 제한되었습니다.")
            
            new_topic = {
                "name": name,
                "keywords": keywords,
                "weight": weight
            }
            
            self.keywords_config["topics"].append(new_topic)
            self.save_keywords()
            self.logger.info(f"새 주제 추가 완료: {name}")
            return True
        
        except Exception as e:
            self.logger.error(f"주제 추가 중 오류: {e}")
            return False
    
    def update_topic(self, topic_name, new_name=None, keywords=None, weight=None):
        """주제 업데이트"""
        try:
            for topic in self.keywords_config["topics"]:
                if topic["name"] == topic_name:
                    # 주제 이름 변경
                    if new_name is not None and new_name.strip():
                        topic["name"] = new_name.strip()
                        self.logger.info(f"주제 이름 변경: {topic_name} → {new_name}")
                    
                    # 키워드 변경
                    if keywords is not None:
                        topic["keywords"] = keywords[:10] # 최대 10개로 제한
                    
                    # 비중 변경
                    if weight is not None:
                        topic["weight"] = weight
                    
                    self.save_keywords()
                    self.logger.info(f"주제 업데이트 완료: {new_name if new_name else topic_name}")
                    return True
            
            self.logger.warning(f"주제를 찾을 수 없습니다: {topic_name}")
            return False
        
        except Exception as e:
            self.logger.error(f"주제 업데이트 중 오류: {e}")
            return False
    
    def remove_topic(self, topic_name):
        """주제 삭제"""
        try:
            self.keywords_config["topics"] = [
                topic for topic in self.keywords_config["topics"] 
                if topic["name"] != topic_name
            ]
            self.save_keywords()
            self.logger.info(f"주제 삭제 완료: {topic_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"주제 삭제 중 오류: {e}")
            return False
    
    def get_topics(self):
        """모든 주제 반환"""
        return self.keywords_config["topics"]
    
    def get_topic_keywords(self, topic_name):
        """특정 주제의 키워드 반환"""
        for topic in self.keywords_config["topics"]:
            if topic["name"] == topic_name:
                return topic["keywords"]
        return []
    
    def get_weighted_topics(self):
        """비중에 따라 정렬된 주제 반환"""
        sorted_topics = sorted(
            self.keywords_config["topics"], 
            key=lambda x: x["weight"], 
            reverse=True
        )
        return sorted_topics[:self.keywords_config["max_topics"]]
    
    def display_topics(self):
        """주제 목록 출력"""
        print("\n현재 설정된 주제 목록:")
        print("=" * 50)
        
        for i, topic in enumerate(self.get_weighted_topics(), 1):
            print(f"{i}. {topic['name']} (비중: {topic['weight']}%)")
            print(f"   키워드: {', '.join(topic['keywords'])}")
            print()
    
    def interactive_setup(self):
        """대화형 키워드 설정"""
        print("뉴스레터 키워드 설정")
        print("=" * 30)
        
        while True:
            print("\n1. 주제 추가")
            print("2. 주제 수정")
            print("3. 주제 삭제")
            print("4. 주제 목록 보기")
            print("5. 설정 완료")
            
            choice = input("\n선택하세요 (1-5): ").strip()
            
            if choice == "1":
                self.add_topic_interactive()
            elif choice == "2":
                self.edit_topic_interactive()
            elif choice == "3":
                self.delete_topic_interactive()
            elif choice == "4":
                self.display_topics()
            elif choice == "5":
                print("설정이 완료되었습니다!")
                break
            else:
                print("잘못된 선택입니다. 다시 선택해주세요.")
    
    def add_topic_interactive(self):
        """대화형 주제 추가"""
        name = input("주제 이름을 입력하세요: ").strip()
        if not name:
            print("주제 이름은 필수입니다.")
            return
        
        keywords_input = input("키워드를 쉼표로 구분하여 입력하세요 (최대 10개): ").strip()
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()][:10]
        
        if not keywords:
            print("키워드는 필수입니다.")
            return
        
        try:
            weight = int(input("비중을 입력하세요 (1-100): ").strip())
            if weight < 1 or weight > 100:
                weight = 20
                print("비중을 20%로 설정합니다.")
        except ValueError:
            weight = 20
            print("비중을 20%로 설정합니다.")
        
        if self.add_topic(name, keywords, weight):
            print(f"주제 '{name}'이(가) 추가되었습니다.")
        else:
            print("주제 추가에 실패했습니다.")
    
    def edit_topic_interactive(self):
        """대화형 주제 수정"""
        self.display_topics()
        topic_name = input("수정할 주제 이름을 입력하세요: ").strip()
        
        if not topic_name:
            return
        
        new_name = input("새 주제 이름을 입력하세요 (변경하지 않으려면 엔터): ").strip()
        keywords_input = input("새 키워드를 쉼표로 구분하여 입력하세요 (엔터로 건너뛰기): ").strip()
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()][:10] if keywords_input else None
        
        weight_input = input("새 비중을 입력하세요 (1-100, 엔터로 건너뛰기): ").strip()
        weight = int(weight_input) if weight_input and weight_input.isdigit() else None
        
        if self.update_topic(topic_name, new_name, keywords, weight):
            print(f"주제 '{topic_name}'이(가) 수정되었습니다.")
        else:
            print("주제 수정에 실패했습니다.")
    
    def delete_topic_interactive(self):
        """대화형 주제 삭제"""
        self.display_topics()
        topic_name = input("삭제할 주제 이름을 입력하세요: ").strip()
        
        if not topic_name:
            return
        
        confirm = input(f"정말로 '{topic_name}' 주제를 삭제하시겠습니까? (y/N): ").strip().lower()
        if confirm == 'y':
            if self.remove_topic(topic_name):
                print(f"주제 '{topic_name}'이(가) 삭제되었습니다.")
            else:
                print("주제 삭제에 실패했습니다.")
        else:
            print("삭제가 취소되었습니다.")

    def update_pick_summary_setting(self, enable=True):
        """PICK 요약 기능 활성화/비활성화 설정"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config['enable_pick_summary'] = enable
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"PICK 요약 기능 {'활성화' if enable else '비활성화'} 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"PICK 요약 설정 업데이트 실패: {e}")
            return False
    
    def get_pick_summary_setting(self):
        """PICK 요약 기능 설정 상태 확인"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return config.get('enable_pick_summary', True)
            
        except Exception as e:
            self.logger.error(f"PICK 요약 설정 확인 실패: {e}")
            return True  # 기본값은 활성화