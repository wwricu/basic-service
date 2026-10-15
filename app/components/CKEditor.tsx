import type { FileLoader, UploadAdapter, UploadResponse } from 'ckeditor5';
import { FileRepository, Plugin } from 'ckeditor5';
import { CKEditor } from '@ckeditor/ckeditor5-react';
import {
  Alignment,
  Heading,
  Font,
  Bold,
  Italic,
  Strikethrough,
  Subscript,
  Superscript,
  Code,
  CodeBlock,
  BlockQuote,
  Highlight,
  List,
  ListProperties,
  Table,
  TableCaption,
  TableToolbar,
  TableLayout,
  TableColumnResize,
  Image,
  ImageToolbar,
  ImageCaption,
  ImageStyle,
  ImageResize,
  LinkImage,
  ImageInsert,
  Emoji,
  Mention,
  Link,
  AutoLink,
  SpecialCharactersEssentials,
  SpecialCharacters,
  FindAndReplace,
  Fullscreen,
  ClassicEditor,
  Essentials,
  GeneralHtmlSupport,
  Paragraph,
} from 'ckeditor5';

import 'ckeditor5/ckeditor5.css';
import '~/styles/ckeditor.css';

import { PostResourceType } from '~/server/domain/enum';
import { uploadFileAPI } from '~/web/api/common';
import { useEffect } from 'react';

declare module '@ckeditor/ckeditor5-core' {
  interface EditorConfig {
    uploader?: CKEditorUploaderConfig;
  }
}

interface CKEditorUploaderConfig {
  postId: string;
  fileType: string;
}

type EditorProps = {
  content: string;
  setContent: (content: string) => void;
  postId?: number;
};

class CKEditorUploader extends Plugin {
  public static override get isOfficialPlugin(): false {
    return false;
  }

  public static override get isPremiumPlugin(): false {
    return false;
  }

  public init(): void {
    const options = this.editor.config.get('uploader');
    if (!options) {
      return;
    }

    this.editor.plugins.get(FileRepository).createUploadAdapter = (loader) => {
      return new CKEditorUploadAdaptor(loader, options);
    };
  }
}

class CKEditorUploadAdaptor implements UploadAdapter {
  public loader: FileLoader;
  readonly fileType: string;
  readonly postId: string;

  constructor(loader: FileLoader, options: CKEditorUploaderConfig) {
    this.fileType = options.fileType;
    this.postId = options.postId;
    this.loader = loader;
  }

  public async upload(): Promise<UploadResponse> {
    return this.loader.file.then(
      (file: File | null) =>
        new Promise<UploadResponse>((resolve, reject) => {
          if (!file) {
            return;
          }

          const formData = new FormData();
          formData.append('post_id', this.postId);
          formData.append('file_type', this.fileType);
          formData.append('file', file, file?.name);

          uploadFileAPI(formData)
            .then((fileUploadVO) => {
              resolve({
                default: fileUploadVO.location,
                name: fileUploadVO.name,
              });
            })
            .catch(() => {
              reject('failed');
            });
        }),
    );
  }
}

export const AboutEditor = ({ content, setContent }: EditorProps) => {
  return (
    <div style={{ flex: 1, minHeight: 0 }}>
      <CKEditor
        editor={ClassicEditor}
        data={content}
        onChange={(_, editor) => setContent(editor.getData())}
        config={{
          licenseKey: 'GPL',
          plugins: [
            Heading,
            Alignment,
            Font,
            Essentials,
            Paragraph,
            Bold,
            Italic,
            Strikethrough,
            Subscript,
            Superscript,
            Highlight,
            Emoji,
            Mention,
            AutoLink,
            Link,
            SpecialCharacters,
            SpecialCharactersEssentials,
            GeneralHtmlSupport,
          ],
          toolbar: {
            items: [
              'heading',
              '|',
              'alignment',
              'fontFamily',
              'fontSize',
              '|',
              'bold',
              'italic',
              'strikethrough',
              'subscript',
              'superscript',
              'highlight',
              '|',
              'emoji',
              'link',
              'specialCharacters',
            ],
            shouldNotGroupWhenFull: true,
          },
        }}
      />
    </div>
  );
};

export const PostEditor = ({ content, setContent, postId }: EditorProps) => {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  });

  return (
    <CKEditor
      editor={ClassicEditor}
      data={content}
      onChange={(_, editor) => setContent(editor.getData())}
      config={{
        licenseKey: 'GPL',
        plugins: [
          Alignment,
          Heading,
          Font,
          Bold,
          Italic,
          Strikethrough,
          Subscript,
          Superscript,
          Code,
          CodeBlock,
          BlockQuote,
          Highlight,
          List,
          ListProperties,
          Table,
          TableCaption,
          TableToolbar,
          TableLayout,
          TableColumnResize,
          Image,
          ImageToolbar,
          ImageCaption,
          ImageStyle,
          ImageResize,
          LinkImage,
          ImageInsert,
          CKEditorUploader,
          Emoji,
          Mention,
          Link,
          AutoLink,
          SpecialCharactersEssentials,
          SpecialCharacters,
          FindAndReplace,
          Fullscreen,
          Essentials,
          GeneralHtmlSupport,
          Paragraph,
        ],
        toolbar: {
          items: [
            'undo',
            'redo',
            '|',
            'alignment',
            'heading',
            '|',
            'fontFamily',
            'fontSize',
            'fontColor',
            'fontBackgroundColor',
            '|',
            'bold',
            'italic',
            'strikethrough',
            'subscript',
            'superscript',
            'code',
            'codeblock',
            'blockquote',
            'highlight',
            '|',
            'bulletedList',
            'numberedList',
            'insertTable',
            'insertImage',
            'emoji',
            'link',
            'specialCharacters',
            '|',
            'findandreplace',
            'fullscreen',
          ],
          shouldNotGroupWhenFull: true,
        },
        table: {
          contentToolbar: [
            'toggleTableCaption',
            'tableColumn',
            'tableRow',
            'mergeTableCells',
          ],
        },
        image: {
          toolbar: [
            'imageStyle:block',
            'imageStyle:side',
            '|',
            'toggleImageCaption',
            'imageTextAlternative',
            '|',
            'linkImage',
          ],
        },
        uploader: {
          postId: postId!.toString(),
          fileType: PostResourceType.IMAGE,
        },
      }}
    />
  );
};
