from django.db import models
from django.contrib.auth.models import User, AbstractUser, Group
from django.db.models.functions import Greatest
from django.utils import timezone

# Create your models here.
class UserInfo(AbstractUser):
    """
    用户信息
    """
    nid = models.AutoField(primary_key=True)
    telephone = models.CharField(verbose_name='电话号码', max_length=11, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    group = models.ForeignKey(to='Group', to_field='nid', on_delete=models.CASCADE, null=True)  # 增加字段没报错
    default_group = models.CharField(verbose_name='默认分组', max_length=10, null=True)
    default_name = models.CharField(verbose_name='默认姓名', max_length=20, null=True)
    default_card = models.CharField(verbose_name='默认卡片', max_length=20, null=True)
    def __str__(self):
        return self.username

class Group(models.Model):
    """
    用户分组
    """
    nid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, verbose_name='权限名称')
    def __str__(self):
        return self.name

class StuInfo(models.Model):
    """
    学生信息
    """
    nid = models.AutoField(primary_key=True)
    student_name = models.CharField(verbose_name='学生姓名', max_length=10)
    sex = models.CharField(verbose_name='性别', max_length=5, null=True)
    telephone = models.CharField(verbose_name='电话号码', max_length=11, null=True)
    # avatar = models.FileField(upload_to='avatar/', default='avatar/default.png')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True)
    modify_time = models.DateTimeField(verbose_name='修改时间', auto_now=True, null=True)

    userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)
    study_status = models.BooleanField(verbose_name='是否在校', default=True)
    school = models.ForeignKey(to='School', to_field='nid', null=True, on_delete=models.CASCADE)

    location = models.ManyToManyField(to="Location", verbose_name='地点')
    grade = models.ManyToManyField(to="Grade", verbose_name='年级')
    tuition_amount = models.ManyToManyField(to="Tuition", verbose_name='学费')

    charge_status = models.IntegerField(verbose_name='交费观察', null=True, default=False)

    def __str__(self):
        return self.student_name


class Tuition(models.Model):
    """
    学生课时费清单
    """
    nid = models.AutoField(primary_key=True)
    student_name = models.ForeignKey(to='StuInfo', null=True, on_delete=models.CASCADE)
    grade = models.ForeignKey(to='Grade', null=True, on_delete=models.CASCADE)
    subject = models.ForeignKey(to='Subject', null=True, on_delete=models.CASCADE)
    tuition_amount = models.IntegerField(verbose_name='学费')
    userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True)
    modify_time = models.DateTimeField(verbose_name='修改时间', auto_now=True, null=True)
    def __str__(self):
        return self.student_name


class StuCharge(models.Model):
    """
    学生收费表
    """
    nid = models.AutoField(primary_key=True)
    charge_date = models.DateField(verbose_name='收费日期')
    charge_amount = models.DecimalField(verbose_name='收费金额', decimal_places=2, max_digits=10)
    note = models.CharField(verbose_name='备注', max_length=30, null=True)
    invoice = models.CharField(verbose_name='发票', max_length=30, null=True)
    status = models.IntegerField(verbose_name='状态', null=True, default=False)

    stuinfo = models.ForeignKey(to='StuInfo', to_field='nid', null=True, verbose_name='学生姓名', on_delete=models.CASCADE)
    

    def __str__(self):
        return f"收费记录 - ¥{self.charge_amount} ({self.charge_date})"


class StuPayInfo(models.Model):
    """
    学生财务信息
    """
    nid = models.AutoField(primary_key=True)
    salary_date = models.IntegerField(verbose_name='月份')
    last_balance = models.DecimalField(verbose_name='上月余额', null=True, decimal_places=2, max_digits=10)
    tuition = models.DecimalField(verbose_name='学费', decimal_places=2, max_digits=10)
    this_balance = models.DecimalField(verbose_name='本月余额', null=True, decimal_places=2, max_digits=10)

    stuinfo = models.ForeignKey(to='StuInfo', to_field='nid', null=True, verbose_name='学生姓名', on_delete=models.CASCADE)

    def __str__(self):
        return self.nid


class TeacherInfo(models.Model):
    """
    教师信息
    """
    nid = models.AutoField(primary_key=True)
    sex = models.CharField(verbose_name='性别', max_length=5, null=True)
    teacher_name = models.CharField(verbose_name='教师姓名', max_length=10)
    telephone = models.CharField(verbose_name='教师电话号码', max_length=11, null=True)
    subject = models.CharField(verbose_name='科目', max_length=10)
    # avatar = models.FileField(upload_to='avatar/', default='avatar/default.png')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    modify_time = models.DateTimeField(verbose_name='修改时间', auto_now=True, null=True)
    others = models.CharField(verbose_name='备注', max_length=100, null=True)
    userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)

    subject = models.ManyToManyField(to="Subject", verbose_name='学科')
    salary = models.ManyToManyField(to="StuInfo", verbose_name='课时费')

    def __str__(self):
        return self.teacher_name


class TeacherPayInfo(models.Model):
    """
    教师财务信息
    """
    nid = models.AutoField(primary_key=True)
    salary = models.DecimalField(verbose_name='课时费', max_digits=10, decimal_places=2)
    salary_date = models.IntegerField(verbose_name='月份')
    payment_status = models.BooleanField(verbose_name='付款状态')
    payment_date = models.DateField(verbose_name='付款日期')

    teacherinfo = models.ForeignKey(to='TeacherInfo', to_field='nid', null=True, verbose_name='教师姓名',
                                    on_delete=models.CASCADE)

    def __str__(self):
        return self.nid


class LessonInfo(models.Model):
    """
    课程信息
    """
    nid = models.AutoField(primary_key=True)
    date = models.DateField(verbose_name='上课日期')
    salary = models.IntegerField(verbose_name='课时费', null=True)
    week = models.CharField(verbose_name='星期', null=True, max_length=15)
    specific_time = models.CharField(verbose_name='具体时间', null=True, max_length=10)
    salary_status = models.BooleanField(verbose_name='付款状态', default=False)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True)
    modify_time = models.DateTimeField(verbose_name='修改时间', auto_now=True, null=True)

    duration = models.IntegerField(verbose_name='持续时间', default=120)

    location = models.ForeignKey(to='Location', to_field='nid', null=True, verbose_name='地点', on_delete=models.CASCADE)
    teacherinfo = models.ForeignKey(to='TeacherInfo', to_field='nid', null=True, verbose_name='教师',
                                    on_delete=models.CASCADE)
    userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)
    subject = models.ForeignKey(to='Subject', to_field='nid', null=True, verbose_name='科目', on_delete=models.CASCADE)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, verbose_name='年级', on_delete=models.CASCADE)
    student = models.ManyToManyField(to="StuInfo", through='lessoninfo_student')
    time = models.ForeignKey(to='lessontime', to_field='nid', null=True, verbose_name='上课时间', on_delete=models.CASCADE)


    def __str__(self):
        return str(self.nid)


class LessonStudentTuition(models.Model):
    """
    记录每节课的学生信息
    """
    nid = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(to='LessonInfo', to_field='nid', verbose_name='课程', on_delete=models.CASCADE)
    student = models.ForeignKey(to='StuInfo', to_field='nid', verbose_name='学生', on_delete=models.CASCADE)
    tuition = models.IntegerField(verbose_name='课时费', null=True)

    def __str__(self):
        return self.nid


class Subject(models.Model):
    """
    学科种类
    """
    nid = models.AutoField(primary_key=True)
    subject_name = models.CharField(verbose_name='学科名称', max_length=5)

    def __str__(self):
        return self.subject_name


class Grade(models.Model):
    """
    年级
    """
    nid = models.AutoField(primary_key=True)
    grade_name = models.CharField(verbose_name='年级名称', max_length=5)

    def __str__(self):
        return self.grade_name


class lessontime(models.Model):
    """
    上课时间
    """
    nid = models.AutoField(primary_key=True)
    lesson_time = models.CharField(verbose_name='上课时间', max_length=5)

    def __str__(self):
        return self.lesson_time


class Location(models.Model):
    """
    地点
    """
    nid = models.AutoField(primary_key=True)
    location_name = models.CharField(verbose_name='地点', max_length=20)
    contact = models.CharField(verbose_name='联系人', max_length=10)
    telephone = models.CharField(verbose_name='联系电话', max_length=50)
    work_status = models.BooleanField(verbose_name='是否在校', default=True)
    address = models.CharField(verbose_name='联系电话', max_length=50, null=True)
    transport = models.CharField(verbose_name='联系电话', max_length=50, null=True)

    userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)

    def __str__(self):
        return self.location_name


class Getsalary(models.Model):
    """
    教师课时费
    """
    nid = models.AutoField(primary_key=True)
    basic_salary = models.IntegerField(verbose_name='基础课时费')
    extra_salary = models.IntegerField(verbose_name='附加课时费')
    extra_number = models.IntegerField(verbose_name='附加人数', default=3)

    teacher_name = models.ManyToManyField(to="TeacherInfo", verbose_name='教师姓名')
    location_name = models.ManyToManyField(to="Location", verbose_name='地点')
    grade_name = models.ForeignKey(to='Grade', to_field='nid', verbose_name='年级', on_delete=models.CASCADE)

    # userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)

    def __str__(self):
        return self.nid


class School(models.Model):
    """
    学校列表
    """
    nid = models.AutoField(primary_key=True)
    school_name = models.CharField(verbose_name='学校名称', max_length=20)
    area = models.CharField(verbose_name='区域', max_length=10)

    def __str__(self):
        return self.school_name


class Prelessons(models.Model):
    """
    从excel导入的预排课数据
    """
    nid = models.AutoField(primary_key=True)
    grade = models.CharField(verbose_name='年级', max_length=10, null=True)
    subject = models.CharField(verbose_name='学科', max_length=10, null=True)
    teacherinfo = models.CharField(verbose_name='教师姓名', max_length=10, null=True)
    location = models.CharField(verbose_name='地点', max_length=10, null=True)
    week = models.CharField(verbose_name='星期', max_length=10, null=True)
    date = models.CharField(verbose_name='日期', max_length=10, null=True)
    time = models.CharField(verbose_name='上课时间', max_length=10, null=True)
    time_specific = models.CharField(verbose_name='上课时间', max_length=10, null=True)
    room = models.CharField(verbose_name='用户', max_length=10, null=True)
    student_name = models.CharField(verbose_name='学生姓名', max_length=1000, null=True)
    # student_number = models.IntegerField(verbose_name='学生人数', null=True)
    prelessons_status = models.BooleanField(verbose_name='是否完成', default=False)

    duration = models.IntegerField(verbose_name='持续时间', default=120)

def __str__(self):
        return self.nid


class lessoninfo_student(models.Model):
    lessoninfo = models.ForeignKey(to='LessonInfo', to_field='nid', on_delete=models.CASCADE)
    stuinfo = models.ForeignKey(to='StuInfo', to_field='nid', on_delete=models.CASCADE, unique=False)
    # tuition = models.CharField(verbose_name='课时费', max_length=10, null=True)
    tuition = models.IntegerField(verbose_name='学费', null=True)

class Icalendar(models.Model):
    """
    日历数据存储
    """
    nid = models.AutoField(primary_key=True)
    classname = models.CharField(verbose_name='课程内容', max_length=20, null=True)
    classtime = models.CharField(verbose_name='课程时间', max_length=2, null=True)
    date = models.CharField(verbose_name='日期', max_length=10, null=True)
    created = models.CharField(verbose_name='创建日期', max_length=20, null=True)
    dtstamp = models.CharField(verbose_name='时间戳', max_length=10, null=True)
    uid = models.CharField(verbose_name='上课时间', max_length=10, null=True)
    starttime = models.CharField(verbose_name='上课时间', max_length=10, null=True)
    endtime = models.CharField(verbose_name='下课时间', max_length=10, null=True)

    def __str__(self):
        return self.nid

class Point_day(models.Model):
    """
    记录日历中的特殊事件
    """
    nid = models.AutoField(primary_key=True)
    date = models.CharField(verbose_name='日期', max_length=10, null=True)
    content = models.CharField(verbose_name='内容', max_length=20, null=True)
    flag = models.CharField(verbose_name='标识', max_length=20, null=True)
    userinfo = models.ForeignKey(to='UserInfo', to_field='nid', null=True, verbose_name='创建人', on_delete=models.CASCADE)
    def __str__(self):
        return str(self.nid)

# homeworkonline

class User_item_data(models.Model):
    """
    记录用户提交数据
    """
    nid = models.AutoField(primary_key=True)
    teacher_item_nid = models.ForeignKey(to='Teacher_item_data', to_field='nid', null=True, verbose_name='教师数据', on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    distribute_time = models.DateTimeField(verbose_name='分发时间', auto_now_add=True, null=True)
    item_list = models.CharField(verbose_name='提交数据', max_length=10000, null=True)
    time_finish = models.CharField(verbose_name='完成时间', max_length=20, null=True)
    time_extend = models.CharField(verbose_name='延长时间', max_length=20, null=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    location = models.ForeignKey(to='Location', to_field='nid', null=True, on_delete=models.CASCADE)
    complete_status = models.BooleanField(verbose_name='完成状态', default=False)
    extend_answer = models.BooleanField(verbose_name='答案延时', default=True, null=True)
    alias = models.CharField(verbose_name='别名', max_length=100, null=True)

    def __str__(self):
        return str(self.nid)


class Teacher_item_data(models.Model):
    """
    记录教师提交数据
    """
    nid = models.AutoField(primary_key=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    item_list = models.CharField(verbose_name='提交数据', max_length=10000, null=True)
    time_finish = models.CharField(verbose_name='完成时间', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    location = models.ForeignKey(to='Location', to_field='nid', null=True, on_delete=models.CASCADE)
    closed_status = models.BooleanField(verbose_name='完成状态', default=False)
    alias = models.CharField(verbose_name='别名', max_length=100, null=True)

    def __str__(self):
        return str(self.nid)


class item_data_users(models.Model):
    """
    记录注册用户信息
    """
    nid = models.AutoField(primary_key=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    location = models.ForeignKey(to='Location', to_field='nid', null=True, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='在校状态', default=True)
    def __str__(self):
        return str(self.nid)


class User_code_item_data(models.Model):
    """
    记录学生口令试题数据
    """
    nid = models.AutoField(primary_key=True)
    teacher_item_nid = models.ForeignKey(to='Teacher_code_item_data', to_field='nid', null=True, verbose_name='教师数据', on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    item_list = models.CharField(verbose_name='提交数据', max_length=10000, null=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    complete_status = models.BooleanField(verbose_name='完成状态', default=False)
    alias = models.CharField(verbose_name='别名', max_length=100, null=True)

    def __str__(self):
        return str(self.nid)


class Teacher_code_item_data(models.Model):
    """
    记录教师口令试题
    """
    nid = models.AutoField(primary_key=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    item_list = models.CharField(verbose_name='提交数据', max_length=10000, null=True)
    code = models.CharField(verbose_name='提交码', max_length=50, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    closed_status = models.BooleanField(verbose_name='完成状态', default=False)
    alias = models.CharField(verbose_name='别名', max_length=100, null=True)

    def __str__(self):
        return str(self.nid)

class User_answer_item_data(models.Model):
    """
    记录学生答题卡
    """
    nid = models.AutoField(primary_key=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    item_list = models.CharField(verbose_name='提交数据', max_length=10000, null=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_item_data(models.Model):
    """
    learning new words data
    """
    nid = models.AutoField(primary_key=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    item_list = models.CharField(verbose_name='提交数据', max_length=100000, null=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    location = models.ForeignKey(to='Location', to_field='nid', null=True, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='在校状态', default=True)
    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_users(models.Model):
    """
    记录单词用户信息
    """
    nid = models.AutoField(primary_key=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    password = models.CharField(verbose_name='密码', max_length=20, null=True)
    grade = models.ForeignKey(to='Grade', to_field='nid', null=True, on_delete=models.CASCADE)
    location = models.ForeignKey(to='Location', to_field='nid', null=True, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='在校状态', default=True)
    coins = models.IntegerField(verbose_name='金币', default=True)
    theme = models.IntegerField(verbose_name='当前主题', default=True)
    passive_magic = models.BooleanField(verbose_name='被动魔法', default=False)
    daily_times = models.IntegerField(verbose_name='日常次数', default=True)
    diamonds = models.FloatField(verbose_name='钻石', default=0.0)
    flowers = models.IntegerField(verbose_name='花朵', default=True)
    earning_half = models.BooleanField(verbose_name='收益减半', default=False)
    
    bark_key = models.CharField(max_length=128, blank=True, null=True)
    wxpusher_uid = models.CharField(max_length=128, blank=True, null=True)
    ntfy_topic = models.CharField(max_length=128, blank=True, null=True)
    complete_status = models.IntegerField(verbose_name='完成状态', default=0) # 修改地狱模式

    listening_number = models.IntegerField(verbose_name='听力数量', default=2)
    writingwords_number = models.IntegerField(verbose_name='默写数量', default=1)

    # jpush_registration_id = models.CharField(
    #     verbose_name='极光设备ID', 
    #     max_length=64, 
    #     null=True, 
    #     blank=True
    # )
    
    viewer_name = models.ManyToManyField(to="Learning_new_words_viewer", verbose_name='监督')
    theme_name = models.ManyToManyField(to="Learning_new_words_theme", verbose_name='已拥有主题')

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_account_data(models.Model):
    """
    单词用户数据
    """
    nid = models.AutoField(primary_key=True)
    synonyms = models.CharField(verbose_name='提交数据', max_length=10000, null=True)
    answers = models.CharField(verbose_name='提交答案', max_length=10000, null=True)
    title = models.CharField(verbose_name='题目', max_length=20, null=True)
    username = models.CharField(verbose_name='用户名', max_length=20, null=True)
    complete_status = models.BooleanField(verbose_name='完成状态', default=False) # 修改地狱模式
    alias = models.CharField(verbose_name='别名', max_length=100, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    rate = models.FloatField(verbose_name='成功次数')
    attempt = models.IntegerField(verbose_name='尝试次数')
    view = models.IntegerField(verbose_name='查看答案次数')
    view_time = models.DateTimeField(verbose_name='查看时间', auto_now_add=True)
    swipe = models.IntegerField(verbose_name='游戏次数')
    coins = models.IntegerField(verbose_name='金币', default=True)
    merge_option = models.BooleanField(verbose_name='拼接选项', default=True)
    none_of_above = models.BooleanField(verbose_name='以上都不对', default=False)
    type = models.IntegerField(verbose_name='试题类型')
    reversd_number = models.IntegerField(verbose_name='中译英数量')
    is_spell_number = models.IntegerField(verbose_name='拼写数量')
    is_review_required = models.IntegerField(verbose_name='是否需要复习', default=0)
    review_time = models.DateTimeField(verbose_name='复习时间', null=True)
    apply_challenge = models.IntegerField(verbose_name='挑战状态', default=0)
    swipe_status = models.IntegerField(verbose_name='预习完成', default=0)

    listening_number = models.IntegerField(verbose_name='听力数量')
    writingwords_number = models.IntegerField(verbose_name='默写数量', default=1)
    

    is_pinned = models.BooleanField(verbose_name='置顶', default=False)


class Learning_new_words_account_log(models.Model):
    """
    单词用户日志
    """
    nid = models.AutoField(primary_key=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    log = models.CharField(verbose_name='提交日志', max_length=10000, null=True)
    title = models.CharField(verbose_name='题目', max_length=20, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    alias = models.CharField(verbose_name='别名', max_length=100, null=True)
    swipe = models.CharField(verbose_name='模式', max_length=10, null=True)
    numberprev = models.IntegerField(verbose_name='回溯次数')
    numbershowanswer = models.IntegerField(verbose_name='显示答案次数')
    numbertransparent = models.IntegerField(verbose_name='透明定时次数')
    submittoken = models.CharField(verbose_name='提交标识', max_length=128, null=True)
    account_data = models.ForeignKey(to='Learning_new_words_account_data', to_field='nid', null=True, on_delete=models.CASCADE)
    complement = models.IntegerField(verbose_name='是否补全', default=0)
    diamondConsume = models.CharField(verbose_name='钻石消费', null=True, max_length=255)
    teacher_mark = models.CharField(verbose_name='挑战教师标记', max_length=10000, null=True)
    apply_challenge = models.BooleanField(verbose_name='挑战状态', default=False)
    complete_status = models.BooleanField(verbose_name='地狱模式', default=False) # 修改地狱模式
    earning_half = models.BooleanField(verbose_name='收益减半', default=False) # 心碎模式
    
    listening_number = models.IntegerField(verbose_name='听力数量')
    writingwords_number = models.IntegerField(verbose_name='默写数量', default=1)
          
    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_account_textbook(models.Model):
    """
    单词用户单词本
    """
    nid = models.AutoField(primary_key=True)
    username = models.CharField(verbose_name='学生名', max_length=20, null=True)
    textbook = models.CharField(verbose_name='提交日志', max_length=10000, null=True)
    modify_time = models.DateTimeField(verbose_name='修改时间', auto_now=True, null=True)
    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_purchase_log(models.Model):
    """
    购买日志
    """
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(to='Learning_new_words_users', to_field='nid', null=True, on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now=True, null=True)
    type = models.CharField(verbose_name='购买类型', max_length=20, null=True)
    coins = models.IntegerField(verbose_name='消费金币', default=0, null=True)
    account_data = models.ForeignKey(to='Learning_new_words_account_data', to_field='nid', null=True, on_delete=models.CASCADE)
    account_log = models.ForeignKey(to='Learning_new_words_account_log', to_field='nid', null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_uncertain(models.Model):
    """
    迟疑库
    """
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(to='Learning_new_words_users', to_field='nid', null=True, on_delete=models.CASCADE)
    vocabulary = models.CharField(verbose_name='延迟词汇', max_length=10000, null=True)
    account_data = models.ForeignKey(to='Learning_new_words_account_data', to_field='nid', null=True, on_delete=models.CASCADE)
    account_log = models.ForeignKey(to='Learning_new_words_account_log', to_field='nid', null=True, on_delete=models.CASCADE)
    type = models.CharField(verbose_name='延迟类型', max_length=20, null=True)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_answer_log(models.Model):
    """
    答案页日志
    """
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(to='Learning_new_words_users', to_field='nid', null=True, on_delete=models.CASCADE)
    account_data = models.ForeignKey(to='Learning_new_words_account_data', to_field='nid', null=True, on_delete=models.CASCADE)
    account_log = models.ForeignKey(to='Learning_new_words_account_log', to_field='nid', null=True, on_delete=models.CASCADE)
    type = models.CharField(verbose_name='行为类型', max_length=20, null=True)
    create_time = models.CharField(verbose_name='发生时间', max_length=50, null=True)
    duration = models.CharField(verbose_name='持续时间', max_length=1000, null=True)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_spell_vocabulary(models.Model):
    """
    拼写词汇
    """
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(to='Learning_new_words_users', to_field='nid', null=True, on_delete=models.CASCADE)
    account_data = models.ForeignKey(to='Learning_new_words_account_data', to_field='nid', null=True, on_delete=models.CASCADE)
    account_log = models.ForeignKey(to='Learning_new_words_account_log', to_field='nid', null=True, on_delete=models.CASCADE)
    type = models.CharField(verbose_name='行为类型', max_length=20, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    data_words = models.CharField(verbose_name='数据', max_length=10000, null=True)
    lock_spell = models.BooleanField(verbose_name='锁定拼写', default=False)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_xlsm(models.Model):
    """
    xlsm文件
    """
    nid = models.AutoField(primary_key=True)
    xlsm_name = models.CharField(verbose_name='文件名称', max_length=128, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    is_distributed = models.BooleanField(verbose_name='锁定拼写', default=True)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_viewer(models.Model):
    """
    xlsm文件
    """
    nid = models.AutoField(primary_key=True)
    viewer_name = models.CharField(verbose_name='监督姓名', max_length=128, null=True)
    password = models.CharField(verbose_name='监督密码', max_length=128, null=True)

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_theme(models.Model):
    """
    主题选择
    """
    nid = models.AutoField(primary_key=True)
    theme_name = models.CharField(verbose_name='主题名称', max_length=128, null=True)

    def __str__(self):
        return str(self.nid)
    
class AudioData(models.Model):
    nid = models.AutoField(primary_key=True)
    word = models.CharField(max_length=255, unique=True)
    audio_blob = models.BinaryField()  # 存二进制音频数据

    def __str__(self):
        return str(self.nid)
    
class Learning_new_words_winningstreak_weekly(models.Model):
    """
    周连胜纪录
    """
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(to='Learning_new_words_users', to_field='nid', null=True, on_delete=models.CASCADE)
    week_monday = models.DateField(verbose_name='周一时间')
    record_count = models.IntegerField(verbose_name='记录数量', default=0)
    complete_state = models.IntegerField(verbose_name='连胜完成', default=0)

    def __str__(self):
        return str(self.nid)

class Learning_new_words_winningstreak_daily(models.Model):
    """
    日连胜纪录
    """
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(to='Learning_new_words_users', to_field='nid', null=True, on_delete=models.CASCADE)
    date = models.DateField(verbose_name='日期')
    record_count = models.IntegerField(verbose_name='记录数量', default=0)

    def __str__(self):
        return str(self.nid)
    
class PushTask(models.Model):
    # 发送信息
    nid = models.AutoField(primary_key=True)
    content = models.TextField(verbose_name='推送内容')
    push_level = models.IntegerField(verbose_name='推送等级')
    scheduled_time = models.DateTimeField(null=True, blank=True, verbose_name='预约时间')
    actual_sent_time = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')
    status = models.BooleanField(default=False, verbose_name='是否执行成功')

class PushRecord(models.Model):
    nid = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        to='Learning_new_words_users', 
        to_field='nid', 
        null=True, 
        on_delete=models.CASCADE,
        db_column='user',  # [新增] 强制指向数据库里叫 user 的那一列
        verbose_name='接收学生'
    )
    task = models.ForeignKey(
        to='PushTask', 
        on_delete=models.CASCADE,
        db_column='task',  # [新增] 强制指向数据库里叫 task 的那一列
        verbose_name='所属任务'
    )
    sent_status = models.BooleanField(default=False)

class dailyCheckinRecords(models.Model):
    
    # 1. 基础信息
    nid = models.AutoField(primary_key=True)
    date = models.DateField(unique=True, verbose_name="打卡日期")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    # 2. 英语阅读 (录入开始和结束页码)
    reading_start = models.IntegerField(null=True, blank=True, verbose_name="阅读开始页")
    reading_end = models.IntegerField(null=True, blank=True, verbose_name="阅读结束页")

    # 3. 数学练习 (题目内容、时长：分、秒)
    math_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="数学练习题目")
    math_min = models.IntegerField(default=0, verbose_name="时长(分)")
    math_sec = models.IntegerField(default=0, verbose_name="时长(秒)")

    # 4. 英语网课 (标题、类型：上/下/全部)
    class_title = models.CharField(max_length=255, null=True, blank=True, verbose_name="网课标题")
    class_type = models.CharField(
        max_length=20, 
        choices=[('上', '上'), ('下', '下'), ('全部', '全部')],
        null=True, 
        blank=True,
        verbose_name="网课类型"
    )
    reading_saved_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读最后保存时间")
    math_saved_at = models.DateTimeField(null=True, blank=True, verbose_name="数学最后保存时间")
    class_saved_at = models.DateTimeField(null=True, blank=True, verbose_name="网课最后保存时间")
    reading_coupon_used_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读免除券使用时间")
    math_coupon_used_at = models.DateTimeField(null=True, blank=True, verbose_name="数学免除券使用时间")
    class_coupon_used_at = models.DateTimeField(null=True, blank=True, verbose_name="网课免除券使用时间")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} 的学习记录"
    
class savedDateRange(models.Model):
    nid = models.AutoField(primary_key=True)
    start_date = models.DateField(verbose_name='开始日期')
    end_date   = models.DateField(verbose_name='结束日期')
    amount = models.DecimalField(verbose_name='金额', max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(verbose_name='领取状态', max_length=20, null=True, blank=True)

    class Meta:
        app_label = 'app01'

class savedExclusions(models.Model):
    """
    保存用户在区间查询中选择的"不统计"项目
    exclusions 字段存储 JSON 数组，元素格式为 "YYYY-MM-DD:section"
    例如：["2026-05-01:reading", "2026-05-03:math"]
    """
    nid        = models.AutoField(primary_key=True)
    exclusions = models.TextField(verbose_name='不统计项目', default='[]')
 
    class Meta:
        app_label = 'app01'
        db_table = 'app01_savedexclusions'

class CouponData(models.Model):
    """
    记录免除券的发放和使用情况
    """
    nid = models.AutoField(primary_key=True)
    total_coupons = models.IntegerField(default=0, verbose_name="总免除券数")
    used_coupons = models.IntegerField(default=0, verbose_name="已用免除券数")
    
    class Meta:
        app_label = 'app01'
        db_table = 'app01_coupondata'

class CouponLog(models.Model):
    """
    记录免除券的消费和增加日志
    """
    nid = models.AutoField(primary_key=True)
    action = models.CharField(max_length=50, verbose_name="操作类型") # add, use, revoke, refund
    amount = models.IntegerField(verbose_name="变动数量(正负)")
    detail = models.CharField(max_length=255, verbose_name="日志详情")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        app_label = 'app01'
        db_table = 'app01_couponlog'
        ordering = ['-create_time']

class RemedyCouponData(models.Model):
    """
    记录补救券的发放和使用情况
    """
    nid = models.AutoField(primary_key=True)
    total_coupons = models.IntegerField(default=0, verbose_name="总补救券数")
    used_coupons = models.IntegerField(default=0, verbose_name="已用补救券数")

    class Meta:
        app_label = 'app01'
        db_table = 'app01_remedycoupondata'

class RemedyCouponLog(models.Model):
    """
    记录补救券的消费和增加日志
    """
    nid = models.AutoField(primary_key=True)
    action = models.CharField(max_length=50, verbose_name="操作类型") # add, use
    amount = models.IntegerField(verbose_name="变动数量(正负)")
    detail = models.CharField(max_length=255, verbose_name="日志详情")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        app_label = 'app01'
        db_table = 'app01_remedycouponlog'
        ordering = ['-create_time']

class RemedyCouponUsage(models.Model):
    """
    记录补救券开启编辑权限的具体日期和项目
    一张补救券只对应一个 date + section。
    """
    nid = models.AutoField(primary_key=True)
    date = models.DateField(verbose_name="补救日期")
    section = models.CharField(max_length=20, verbose_name="补救项目")
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="使用时间")
    saved_at = models.DateTimeField(null=True, blank=True, verbose_name="补救保存时间")

    class Meta:
        app_label = 'app01'
        db_table = 'app01_remedycouponusage'
