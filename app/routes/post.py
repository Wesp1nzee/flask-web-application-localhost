from flask import Blueprint, render_template, request, session, jsonify
from ..models.post import News, Comment, Reaction
from ..extensions import db
from ..forms import CommentForm, ReactionForm
from ..utils.utils import login_required

post = Blueprint('post', __name__, template_folder='templates')
post.static_folder = 'static'

@post.route('/news')
def news_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    news_pagination = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('news_list.html', pagination=news_pagination)

@post.route('/news/<int:news_id>', methods=['GET'])
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    comments = Comment.query.filter_by(news_id=news_id).order_by(Comment.created_at.desc()).all()
    like_count = Reaction.query.filter_by(news_id=news_id, type='like').count()
    dislike_count = Reaction.query.filter_by(news_id=news_id, type='dislike').count()

    comment_form = CommentForm()
    reaction_form = ReactionForm()

    return render_template('news_detail.html', 
                           news=news, 
                           comments=comments, 
                           like_count=like_count, 
                           dislike_count=dislike_count, 
                           comment_form=comment_form, 
                           reaction_form=reaction_form
                           )

@post.route('/news/<int:news_id>/comment', methods=['POST'])
@login_required
def add_comment(news_id):
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comment(
            content=form.content.data,
            user_id=session['user_id'],
            news_id=news_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': 'Comment added successfully', 'comment': {
            'content': new_comment.content,
            'user_id': new_comment.user_id,
            'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }}), 201
    return jsonify({'errors': form.errors}), 400

@post.route('/news/<int:news_id>/react', methods=['POST'])
@login_required
def add_reaction(news_id):
    form = ReactionForm()
    if form.validate_on_submit():
        existing_reaction = Reaction.query.filter_by(user_id=session['user_id'], news_id=news_id).first()
        if existing_reaction:
            existing_reaction.type = form.type.data
        else:
            new_reaction = Reaction(
                type=form.type.data,
                user_id=session['user_id'],
                news_id=news_id
            )
            db.session.add(new_reaction)
        db.session.commit()
        like_count = Reaction.query.filter_by(news_id=news_id, type='like').count()
        dislike_count = Reaction.query.filter_by(news_id=news_id, type='dislike').count()
        return jsonify({'message': 'Reaction added successfully', 'like_count': like_count, 'dislike_count': dislike_count}), 201
    return jsonify({'errors': form.errors}), 400
