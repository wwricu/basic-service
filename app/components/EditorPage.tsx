import React, { useEffect, useState } from 'react';
import { getPostDetailAPI, updatePostDetailAPI } from '~/web/api/post';
import { getAllTag } from '~/web/api/tag';
import {
  Button,
  Flex,
  type GetProp,
  Image,
  Input,
  message,
  Popconfirm,
  Select,
  Upload,
  type UploadProps,
} from 'antd';
import type { PostDetailVO, PostUpdateRO, TagVO } from '~/server/domain/types';
import { PostResourceType, PostStatus, TagType } from '~/server/domain/enum';
import { DownOutlined, LoadingOutlined, PlusOutlined, UpOutlined } from '@ant-design/icons';
import ImgCrop from 'antd-img-crop';
import { useParams } from 'react-router';
import { PostEditor as CKEditor } from './CKEditor';

const { TextArea } = Input;

type TagItem = {
  value: number;
  label: string;
};

type FileType = Parameters<GetProp<UploadProps, 'beforeUpload'>>[0];

const getBase64 = (img: FileType, callback: (url: string) => void) => {
  const reader = new FileReader();
  reader.addEventListener('load', () => callback(reader.result as string));
  reader.readAsDataURL(img);
};

const beforeUpload = (file: FileType) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('You can only upload JPG/PNG file!');
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('Image must smaller than 2MB!');
  }
  return isJpgOrPng && isLt2M;
};

export default function EditorPage() {
  const [title, setTitle] = useState('');
  const [postStatus, setPostStatus] = useState<PostUpdateRO['status']>();
  const [category, setCategory] = useState<TagItem>();
  const [tags, setTags] = useState<TagItem[]>([]);
  const [preview, setPreview] = useState<string>('');
  const [content, setContent] = useState<string>('');
  const [coverId, setCoverId] = useState<number>();
  const [imageUrl, setImageUrl] = useState<string>();

  const [allTags, setAllTags] = useState<TagItem[]>([]);
  const [allCategories, setAllCategories] = useState<TagItem[]>([]);

  const [hidePublishOption, setHidePublishOption] = useState<boolean>(true);
  const [messageApi, contextHolder] = message.useMessage();
  const [loading, setLoading] = useState(false);
  const { id } = useParams();
  const postId = parseInt(id!);

  const onChange: UploadProps['onChange'] = (info) => {
    if (info.file.status === 'uploading') {
      setLoading(true);
      return;
    }
    if (info.file.status === 'done') {
      // Get this url from response in real world.
      getBase64(info.file.originFileObj as FileType, (url) => {
        setLoading(false);
        setImageUrl(url);
      });
      setCoverId(info.file.response.id);
    }
  };

  const updatePost = (status: PostUpdateRO['status']) => {
    const postUpdateRO: PostUpdateRO = {
      id: postId,
      title: title,
      cover_id: coverId,
      content: content,
      preview: preview,
      category_id: category?.value,
      tag_id_list: tags.map((tagItem) => tagItem.value),
      status: status
    };
    updatePostDetailAPI(postUpdateRO).then(() => {
      messageApi.info('success');
    });
  };

  useEffect(() => {
    getAllTag(TagType.POST_TAG).then((tagList: TagVO[]) => {
      const tagItems = tagList.map((tag) => {
        return {
          value: tag.id,
          label: tag.name,
        };
      });
      setAllTags(tagItems);
    });
    getAllTag(TagType.POST_CAT).then((tagList: TagVO[]) => {
      const tagItems = tagList.map((tag) => {
        return {
          value: tag.id,
          label: tag.name,
        };
      });
      setAllCategories(tagItems);
    });

    getPostDetailAPI(postId).then((postDetailVO: PostDetailVO) => {
      setTitle(postDetailVO.title ?? '');
      setPostStatus(postDetailVO.status ?? undefined);
      setContent(postDetailVO.content);
      setCoverId(postDetailVO.cover?.id);
      setImageUrl(postDetailVO.cover?.url);
      setPreview(postDetailVO.preview);

      if (postDetailVO.category) {
        setCategory({ label: postDetailVO.category.name, value: postDetailVO.category.id });
      }

      if (postDetailVO.tag_list?.length > 0) {
        setTags(
          postDetailVO.tag_list.map((tagVO: TagVO) => {
            return {
              label: tagVO.name,
              value: tagVO.id,
            };
          })
        );
      }

      document.title = `Admin - ${postDetailVO.title} - wwr.icu`;
    });
  }, [postId]);

  const moreOptionPanel = (
    <Flex vertical gap='small' style={{ paddingTop: 16, paddingBottom: 16, ...(hidePublishOption ? { display: 'none' } : {}) }}>
      <Select<TagItem>
        showSearch
        allowClear
        labelInValue
        placeholder='No Category'
        optionFilterProp='label'
        value={category}
        options={allCategories}
        onChange={(value) => {
          setCategory(value);
        }}
      />
      <Select<TagItem[]>
        showSearch
        labelInValue
        allowClear
        mode='multiple'
        placeholder='No Tag'
        optionFilterProp='label'
        value={tags}
        onChange={(values) => {
          setTags(values);
        }}
        options={allTags}
      />
      <Flex justify='start' gap='small' className='max-sm-flex-wrap'>
        <Flex vertical align='center' gap='small'>
          <ImgCrop showReset rotationSlider zoomSlider minZoom={0.5} aspect={2}>
            <Upload
              name='file'
              listType='picture-card'
              showUploadList={false}
              action='/api/post/upload'
              maxCount={1}
              beforeUpload={beforeUpload}
              onChange={onChange}
              data={() => ({
                post_id: postId,
                file_type: PostResourceType.COVER_IMAGE,
              })}
              openFileDialogOnClick={coverId === undefined || imageUrl === undefined}
            >
              {imageUrl ? (
                <Image src={imageUrl} alt='cover' />
              ) : loading ? (
                <LoadingOutlined style={{ fontSize: '24px' }} />
              ) : (
                <PlusOutlined style={{ fontSize: '24px' }} />
              )}
            </Upload>
          </ImgCrop>
          <Popconfirm
            title='Sure to reset cover?'
            onConfirm={() => {
              setCoverId(undefined);
              setImageUrl(undefined);
            }}
          >
            <Button style={{ width: '100%' }}>Reset cover</Button>
          </Popconfirm>
        </Flex>
        <TextArea
          style={{ resize: 'none', minHeight: 140 }}
          showCount
          maxLength={200}
          onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
            setPreview(e.target.value);
          }}
          value={preview}
          placeholder='Preview'
        />
      </Flex>
    </Flex>
  );

  return (
    <>
      {contextHolder}
      <Flex vertical gap='small' style={{ padding: 4, paddingBottom: 0, width: '100%', height: '100vh' }}>
        <Input value={title} onChange={(e) => setTitle(e.target.value)}></Input>
        <Flex wrap justify='start' align='center' gap='small'>
          <Button
            style={{ flex: '1 1 0' }}
            icon={hidePublishOption ? <DownOutlined /> : <UpOutlined />}
            onClick={() => setHidePublishOption(!hidePublishOption)}
          >
            More Options
          </Button>
          <Popconfirm title='Sure to save change?' onConfirm={() => updatePost(postStatus!)}>
            <Button style={{ flex: '1 1 0' }} variant='solid' color={postStatus === PostStatus.DRAFT ? 'primary' : 'danger'}>
              Save {postStatus} post
            </Button>
          </Popconfirm>
        </Flex>
        {moreOptionPanel}
        <div style={{ flex: 1, minHeight: 0 }}>
          <CKEditor content={content} setContent={(editorContent) => setContent(editorContent)} postId={postId} />
        </div>
      </Flex>
    </>
  );
}
