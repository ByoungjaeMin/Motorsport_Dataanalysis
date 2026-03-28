import os
import matplotlib.pyplot as plt

DEFAULT_SAVE_DIR = 'Saved_photos'

def ensure_save_dir(path: str = DEFAULT_SAVE_DIR):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def make_filename(session, suffix: str = '') -> str:
    """Make standardized filename: Year_EventName_session[_suffix].png

    `suffix` should not include extension.
    """
    year = getattr(session.event, 'year', '')
    event = getattr(session.event, 'EventName', '')
    session_name = getattr(session, 'name', '')
    base = f"{year}_{event.replace(' ', '_')}_{session_name}"
    if suffix:
        return f"{base}_{suffix}.png"
    return f"{base}.png"

def save_figure(fig, filename: str, save_dir: str = DEFAULT_SAVE_DIR, dpi: int = 300,
                facecolor='white', bbox_inches='tight', show: bool = True, tight_rect=None):
    """Save figure to standardized directory.

    - `fig`: matplotlib Figure object
    - `filename`: just the file name (with .png)
    - `facecolor`: background color for saved PNG (default: 'white')
    - `show`: whether to call `plt.show()` after saving. If False, closes the figure.
    """
    ensure_save_dir(save_dir)
    try:
        if tight_rect is not None:
            fig.tight_layout(rect=tight_rect)
        else:
            fig.tight_layout()
    except Exception:
        pass
    path = os.path.join(save_dir, filename)
    fig.savefig(path, dpi=dpi, bbox_inches=bbox_inches, facecolor=facecolor)
    print(f"[System] Saved: {path}")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return path
