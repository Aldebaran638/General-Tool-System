from app.modules.registry import register_module
from app.modules.workbench.work_report.models import (
    TaskSummary,
    WorkPlan,
    WorkReport,
    WorkReportFieldConfig,
    WorkReportReminderDelivery,
    WorkReportReminderRule,
    WorkReportReminderRuleRecipient,
    WorkReportReminderRun,
    WorkReview,
)
from app.modules.workbench.work_report.router import router

register_module(
    name="work_report",
    group="workbench",
    router=router,
    models=[
        WorkReport,
        WorkPlan,
        TaskSummary,
        WorkReview,
        WorkReportFieldConfig,
        WorkReportReminderRule,
        WorkReportReminderRuleRecipient,
        WorkReportReminderRun,
        WorkReportReminderDelivery,
    ],
)
