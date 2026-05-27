from typing import List, Optional

from src.domain.mentor.model.experience_model import ExperienceVO


# Experiences live inline on profiles.experiences (JSONB[]) — there is no
# separate experiences DAO. The only logic that survived the cutover is the
# pair of derived-flag helpers, which the profile upsert path calls before
# writing the row. Keeping them here (as opposed to inlining or moving) lets
# `ExperienceService.is_mentor(...)` keep working as a stable import path
# for callers that already reference it.
class ExperienceService:

    # Onboarding completion gate. Mentee onboarding writes profiles.want_tags;
    # have_tags is mentor-only and stays empty for plain mentees, so checking
    # want_tags alone is sufficient.
    @staticmethod
    def is_onboarded(want_tags: Optional[List[str]]) -> bool:
        return bool(want_tags)

    # 是否為 Mentor, 透過是否有填寫足夠的經驗類別判斷
    @staticmethod
    def is_mentor(experiences: List[ExperienceVO]) -> bool:
        exp_categories = set()
        for exp in experiences:
            if exp.category:
                exp_categories.add(exp.category)

        # 如果有填寫至少 2 種經驗類別, 則視為已完成 Mentor
        return (len(exp_categories) >= 2)
