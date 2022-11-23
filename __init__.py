
"""

правила:
файл текстового формата .txt с колонками разделенными через Tab
1. сначала идут строки где первая колонка содержит *
    поля:
        name
        category-<num> (1 <= <num> <= 4, каждая подкатегория разделена символом |)
        desk-stats-<num> (1 <= <num> <= 1)
            потенциально <num> - внутренний номер
2. следует ряд с названиями колонок
    Text 1	Text 2	Text 3	Text 4	Text 5	Picture 1	Picture 2	Picture 3	Picture 4	Picture 5	Category 1	Category 2	Category 3	Category 4	Notes	Extra Info
3. далее идут сами карточки
    Text - допускает некоторые html теги
        New line: to create a new/blank line in the flashcard text, enter a "|" (pipe character) or use the <br> tag.
         (If you need this symbol in your text, use a similar Unicode character: ∣ )
        Bold: <b>This will be Bold</b>
        Italics: <i>This will be Italicized</i>
        Underline: <u>This will be Underlined</u>
        Text Color: <color red>This will be Red</color>
             <color #0000FF>This will be Blue</color>   (You can read about color names and codes here.)
        Superscript: <sup>This will be Superscript</sup>
        Subscript: <sub>This will be Subscript</sub>
        Center: <center>This will be centered</center> (assuming the rest of the side is left justified)
        Bullet points: Just copy this into your own text: • and use | (shift \) to create new lines.

        Setting font size: While you can set font size for each side within the app, if you want more control for specific text, you can use <size> tags:
            <size .5>This will be half size</size>
            <size 2>This will be double size</size>
            <size 40>This will be a 40 point font (greater than 5 is a specific size)</size>
        Multiple spaces can be used together using: <sp>
    Picture - имеет свое форматирование. При импорте - можно указывать любое имя. Главное потом отдельно загрузить через приложение соответствующие файлы.
        _0038_2p = _<some-internal-num>_<1 <= num <= 5>.<file-format>
            <some-internal-num> - не получиться определить
            <1 <= num <= 5> - соответствует стороне.
                Если не будет поля Text с таким же номером, то скорее всего будет ошибка
                Если будет пропущен какой - то номер скорее всего будет ошибка
            <file-format> - поддерживаемые?
    Sound - поддерживаются так же файлы звука. Правила сходные с Picture
    Category - должны быть из списка указанного в начале файла. разделены "; "
        Если не из списка - скорее всего будет ошибка
    Notes - заметки
        - текстовое поле
    Extra Info - доп информация
        - текстовое поле

задачи пакета:
    создать объект который можно наполнить данными
    создать контейнер который можно конвертировать в текстовый файл
        все указанные файлы группируются в зип архив

TODO проверка присутствия chosen категорий в full (при добавлении?)
TODO импорт напрямую в sqlite3 базу Files/Flashcard.sql
TODO Взаимодействие с файлами для одновременной упаковки с добавлением имен (проверки включительно)

проверить возможность:
    создать зип архив из нескольких файлов


Варианты испльзования:
    obj = FlashCardsContainer()
    for text1, text2 in some_gen():
        fl_cd= obj.FlashCard() # принцип - все необходимые классы берутся из самого объекта
        s1 = fl_cd.Side(text=text1)
        s2 = fl_cd.Side(text=text2)
        fl_cd.sides += [s1,s2]
        obj.append(fl_cd)
"""
from abc import ABCMeta, abstractmethod, abstractproperty
import pathlib
import zipfile
from dataclasses import dataclass, field, asdict


def zip_files_(list_: list[pathlib.Path], target_zip_path: pathlib.Path):
    not_acceptable = []
    acceptable = []
    names = set()
    for i in list_:
        if i.name not in names:
            acceptable.append(i)
        else :
            not_acceptable.append(i)
        names.add(i.name)

    with zipfile.ZipFile(target_zip_path) as zf:
        for fl in acceptable:
            with zf.open(fl.name, 'wb') as w_fl:
                w_fl.write(fl.read_bytes())

    return not_acceptable


class FlashCardsContainer(list):
    @dataclass
    class Category:
        class Typical(dict):
            class Empty:
                pass
            class _Entry(set, metaclass=ABCMeta):
                sep = abstractproperty()
                def __init__(self, base_line: str =None):
                    super().__init__()
                    if base_line is not None:
                        self.update({
                            i.strip()
                            for i
                            in base_line.split(self.sep)
                        })

                @property
                def asset(self):
                    return set(self)

                def __str__(self):
                    return self.sep.join(self)


            class Config(_Entry):
                sep = "|"
            class Data(_Entry):
                sep = "; "

            def __init__(self):
                super().__init__()
                for i in range(1,4+1):
                    self[str(i)] = self.Empty

            @property
            def is_empty(self) -> bool:
                return all([
                    i == self.Empty
                    for key, i in self.items()
                ])

        cont: Typical[str: set | Typical.Empty] = field(default_factory=Typical)

        @property
        def is_empty(self) -> bool:
            return len(self.cont) == 0

        def fill_default(self):
            for i in range(1,4+1):
                self.cont[str(i)] = self.Typical.Config()

        def __str__(self):
            tot = []
            for num, cont in self.cont.items():
                if cont == self.Typical.Empty:
                    continue
                line = str(cont)
                if isinstance(cont, self.Typical.Config):
                    line = f'*\tcategory-{num}\t{cont}'
                tot.append(line)
            return '\n'.join(tot)

        def as_dict(self, is_set_internal:bool = False):
            tmp = {}
            for num, cont in self.cont.items():
                cont = ''
                if cont != self.Typical.Empty:
                    if is_set_internal:
                        cont = cont.asset
                    else :
                        cont = str(cont)

                tmp[f'Category {num}'] = cont
            return tmp

    @dataclass
    class FlashCard:
        @dataclass
        class Side:
            class Empty:
                pass

            text: str = None
            picture: pathlib.Path | None = None
            sound: pathlib.Path | None = None
            additional_convertion: any = lambda x: x

            @property
            def is_empty(self):
                itms = [self.text, self.picture, self.sound]
                is_None = [i is None for i in itms]
                is_empty = [i == '' if isinstance(i, str) else True for i in itms]
                tot = [i or j for i, j in zip(is_None, is_empty)]
                return all(tot)

            @property
            def convert_text(self):
                # каким текст будет на карточке.
                #? возможно для ключевых слов добавить подсветку
                tmp = str(self.text) \
                    .replace('\t', '<sp>' * 2) \
                    .replace(' '*4, '<sp>' * 2) \
                    .replace('\n', '<br>')
                tmp = self.additional_convertion(tmp)
                return tmp

        sides: list[Side] = field(default_factory=list)
        # отказоустойчивость - идет по порядку и останавливается на 5
        chosen_categories: dict[str:set] = None
        notes: str = None
        extra_info: str = None

    @dataclass
    class Statistic:
        base_line: str = None
        num: str = None

        class NotDefined(BaseException):
            pass

        def __str__(self):
            if self.base_line is not None:
                return f'*\tdeck-stats-{self.num}\t{self.base_line}'
            else:
                raise self.NotDefined

    class DataColumnsMapping:
        default = ['Text 1', 'Text 2', 'Text 3', 'Text 4', 'Text 5',
                   'Picture 1', 'Picture 2', 'Picture 3', 'Picture 4', 'Picture 5',
                   'Category 1', 'Category 2', 'Category 3', 'Category 4',
                   'Notes', 'Extra Info']

        def __init__(self, base_items_line: list[str] = None):
            self.base_items_line = list(self.default) if base_items_line is None else base_items_line

        def __str__(self):
            return '\t'.join(self.base_items_line)

    default_deck_name = 'InitialDeckName'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_categories: FlashCardsContainer.Category = self.Category()
        self.desc_name: str | None = self.default_deck_name
        self.stats: FlashCardsContainer.Statistic | None = self.Statistic()
        self.columns_mapping: FlashCardsContainer.DataColumnsMapping | None = self.DataColumnsMapping()

    def add_flashCard_by_item_line(self, item_line: list[str]):
        # отказоустойчивость - пустые слайды программа пропускает ...
        prep = {
            name: value
            for name, value
            in zip(self.columns_mapping.base_items_line, item_line)
        }
        card_obj = FlashCardsContainer.FlashCard()
        tmp = []
        for num in range(1, 5 + 1):
            tmp_side = card_obj.Side(
                text=prep.get(f'Text {num}', None),
                picture=prep.get(f'Picture {num}', None),
                sound=prep.get(f'Sound {num}', None)
            )
            if tmp_side.is_empty:
                # break
                tmp_side = card_obj.Side.Empty
            tmp.append(tmp_side)
        tmp_catg = self.Category()
        for num in range(1, 4 + 1):
            if any([
                (val_ := prep.get(f'Category {num}', None)) is None,
                val_ == ''
            ]):
                # break
                tmp_catg.cont[str(num)] = self.Category.Typical.Empty
                continue

            tmp_catg.cont[str(num)] = self.Category.Typical.Data(base_line=val_)

        card_obj.sides = tmp
        card_obj.chosen_categories = tmp_catg
        card_obj.notes = prep.get(f'Notes', '')
        card_obj.extra_info = prep.get('Extra Info', '')
        self.append(card_obj)

    def extract_item_line_from_flashcard(self, card_obj: FlashCard, cats: Category = None) -> list[str]:
        tmp = {
            "Notes":card_obj.notes,
            'Extra Info':card_obj.extra_info
        }
        for num, side in enumerate(card_obj.sides, 1):
            if side == card_obj.Side.Empty:
                continue
            tmp.update({
                f'{key.capitalize()} {num}':(value if key!='text' else side.convert_text) if value != card_obj.Side.Empty else ''
                for key, value in asdict(side).items()
            })
        if cats is not None:
            ch_cats = card_obj.chosen_categories.as_dict(is_set_internal=True)
            for key, set in ch_cats:
                cats.cont[key].update(set)
        if card_obj.chosen_categories is not None:
            tmp.update(card_obj.chosen_categories.as_dict())
        prep = [
            '' if (val:=tmp.get(base_col_name, '')) is None else val
            for base_col_name
            in self.columns_mapping.base_items_line
        ]
        return prep

    def __str__(self):
        data = [
            '\t'.join(self.extract_item_line_from_flashcard(card_obj))
            for card_obj in self
        ]
        tmp = []
        if self.full_categories.is_empty:
            self.full_categories.fill_default()
        cards = [
                '\t'.join(self.extract_item_line_from_flashcard(
                    card_obj,
                    self.full_categories if self.full_categories.is_empty else None
                ))
                for card_obj in self
            ]
        tmp.append(f'*\tname\t{self.desc_name}')
        full_cat = str(self.full_categories)
        if full_cat != '':
            tmp.append(full_cat)
        try:
            tmp.append(str(self.stats))
        except self.Statistic.NotDefined:
            'no element inserted'
        tmp.append(str(self.columns_mapping))
        tmp += cards

        return '\n'.join(tmp)


class Parser:
    sep = '\t'

    class LineParser(ABCMeta):
        class NotAcceptable(BaseException):
            pass

        #@classmethod
        @abstractmethod
        def parse(cls, item_line: list[str],  obj: FlashCardsContainer) -> NotAcceptable | None:
            pass

    class ConfigLine(LineParser):
        pass

    class NameLine(ConfigLine):
        @classmethod
        def parse(cls, item_line: list[str], obj: FlashCardsContainer):
            if any([
                item_line[0].strip() != '*',
                item_line[1].strip().lower() != 'name',
                item_line[2] == ''
            ]):
                raise cls.NotAcceptable(f'Name')
            obj.desc_name = item_line[2].strip()

    class CategoryLine(ConfigLine):
        @classmethod
        def parse(cls, item_line: list[str], obj: FlashCardsContainer):
            if any([
                item_line[0].strip() != '*',
                not (catg:= item_line[1].strip().lower()).startswith('category-'),
                not (catg_num:=catg.replace('category-','')).isdecimal(),
                item_line[2] == ''
            ]):
                raise cls.NotAcceptable(f'Category')
            #all_ent = {i.strip() for i in item_line[2].split('|')}
            obj.full_categories.cont[catg_num] = \
                obj.full_categories.Typical.Config(item_line[2])

    class StatsLine(ConfigLine):
        @classmethod
        def parse(cls, item_line: list[str], obj: FlashCardsContainer):
            if any([
                item_line[0].strip() != '*',
                not (stat:= item_line[1].strip().lower()).startswith('deck-stats-'),
                not (stat_num:=stat.replace('deck-stats-','')).isdecimal(),
                item_line[2] == ''
            ]):
                raise cls.NotAcceptable(f'Stats')
            obj.stats = obj.Statistic(base_line=item_line[2], num=stat_num)

    class ColumnsMappingLine(LineParser):
        @classmethod
        def parse(cls, item_line: list[str], obj: FlashCardsContainer):
            if any([
                'text' not in item_line[0].lower(),
                any([itm == '' for itm in item_line])
            ]):
                raise cls.NotAcceptable(f'Columns mapping')
            obj.columns_mapping = obj.DataColumnsMapping(base_items_line=item_line)

    class CardLine(LineParser):
        @classmethod
        def parse(cls, item_line: list[str], obj: FlashCardsContainer):
            #if False: raise cls.NotAcceptable(f'Columns mapping')
            obj.add_flashCard_by_item_line(item_line=item_line)


    class BadConfig(BaseException):
        pass

    class NotAcceptableData(BaseException):
        pass

    @classmethod
    def parse(cls, file: pathlib.Path) -> FlashCardsContainer:
        text = file.read_text(encoding='utf-8')
        name_is_observed = False
        first_column_mapping = False
        data_lines_flag = False
        cont = FlashCardsContainer()
        for line in text.split('\n'):
            item_line = [item.strip() for item in line.split(cls.sep)]
            if not data_lines_flag:
                for sub_cls in cls.ConfigLine.__subclasses__(cls.ConfigLine):
                    try:
                        sub_cls.parse(item_line, cont)
                        if sub_cls is cls.NameLine:
                            name_is_observed = True
                        break
                    except cls.LineParser.NotAcceptable:
                        continue
                else:
                    if not name_is_observed:
                        raise cls.BadConfig
                    else :
                        data_lines_flag = True
                if not data_lines_flag:
                    continue
            if data_lines_flag and not first_column_mapping:
                cls.ColumnsMappingLine.parse(item_line, cont)
                first_column_mapping = True
                continue
            if data_lines_flag:
                try:
                    cls.CardLine.parse(item_line,cont)
                except cls.LineParser.NotAcceptable:
                    print(f'card line (skipped due wrong format): {line} ')
        return cont
