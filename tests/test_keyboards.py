import keyboards as kb


def test_labels_cover_all_options():
    groups = [kb.SPHERE, kb.TASK, kb.BUDGET, kb.TIMELINE]
    for group in groups:
        for key, label in group:
            assert key in kb.LABELS
            assert kb.LABELS[key] == label


def test_start_kb_has_begin():
    kb_markup = kb.start_kb()
    btn = kb_markup.inline_keyboard[0][0]
    assert btn.callback_data == "begin"


def test_sphere_kb_no_back():
    markup = kb.sphere_kb()
    # last row should not contain "back"
    all_data = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert "back" not in all_data


def test_task_kb_has_back():
    markup = kb.task_kb()
    all_data = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert "back" in all_data
