from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["title"], name="library_boo_title_c38ef2_idx"),
        ),
        migrations.AddIndex(
            model_name="book",
            index=models.Index(fields=["author"], name="library_boo_author_66aacb_idx"),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["name"], name="library_mem_name_e66984_idx"),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(fields=["email"], name="library_mem_email_06dc66_idx"),
        ),
        migrations.AddIndex(
            model_name="loan",
            index=models.Index(
                fields=["returned_on", "due_on"],
                name="library_loa_returne_f23db1_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="loan",
            index=models.Index(
                fields=["borrowed_on"],
                name="library_loa_borrowe_ff8bcc_idx",
            ),
        ),
    ]
