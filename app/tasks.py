from datetime import datetime
from flask import current_app
from app import app as flask_app          # <-- use the global app you already create
from app.models import db, Post, PostPlatform  # adjust imports to your paths

# Create one global app for worker context
flask_app.app_context().push()


#! publish_post ///////////////////////////////////////////////////////////////////////////    
def publish_post(post_id: int):
    """
    Idempotent publish: if already published or canceled, do nothing.
    """
    current_app.logger.info(f"[tasks.publish_post] start post_id={post_id}")
    # 1. Finds the post by ID
    post = Post.query.get(post_id)
    
    if not post:
        current_app.logger.warning(f"post {post_id} not found")
        return
    
    # 2. Checks if already published/canceled (idempotent)
    if post.status in ("published", "canceled"):
        current_app.logger.info(f"post {post_id} status={post.status}, skip")
        return

    '''
    This "example" section is only there so you can test the flow end-to-end (schedule → enqueue → worker → database update) without yet writing the real integrations for LinkedIn, X, Instagram, etc.

    For production → you'll replace that part with actual API calls to each platform.
    '''
    
    # 3. Gets all platform connections for the post
    platforms = PostPlatform.query.filter_by(post_id=post.id).all()
    
    # 4. Simulates publishing to each platform
    # TODO: call each platform adapter (X/Twitter, LinkedIn, IG, etc.) IMPORTANT: IMPORTANT <-------- thing to do here TO BE ADDD ONCE INTEGRATIONS ARE ADDED ///////////////////////////////
    # For now, simulate success:
    for pp in platforms:
        pp.status = "published"
        pp.platform_post_id = f"mock:{pp.platform}"
        pp.published_at = datetime.utcnow()
    
    # 5. Updates statuses to "published"    
    post.status = "published"
    post.published_at = datetime.utcnow()
    
    # 6. Sets mock platform_post_ids (done above in the loop)
    # 7. Commits all changes
    db.session.commit()
    current_app.logger.info(f"[tasks.publish_post] done post_id={post_id}")

    #1 test message to see if the worker is working 

def echo(msg: str):
    current_app.logger.info(f"[echo] {msg}")
    return msg
